"""
Chat Service for processing natural language commands - Database Version.
"""

import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from models.api_models import ChatResponse, ProductCreateRequest, ProductEditRequest
from services.database_service import DatabaseService
from services.inventory_agent import InventoryAgent
from utils.email_utils import send_analysis_report


logger = logging.getLogger(__name__)

# Global cache for analysis data (simple in-memory cache)
_analysis_cache = {
    "last_analysis_type": None,
    "last_analysis_data": None,
    "timestamp": None,
}


class ChatService:
    """Service for processing chat messages and commands."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.db_service = DatabaseService(session)
        self.inventory_agent = InventoryAgent(session)
        self.category_mapping = {
            "electrónicos": "Electronics",
            "electrodomésticos": "Appliances",
            "muebles": "Furniture",
            "ropa": "Clothing",
            "deportes": "Sports",
            "libros": "Books",
            "comida": "Food",
            "hogar": "Home",
            "juguetes": "Toys",
            "salud": "Health",
            "automotriz": "Automotive",
            "jardín": "Garden",
        }

    def _save_analysis_to_cache(self, analysis_type: str, analysis_data: dict):
        """Save analysis data to global cache."""
        global _analysis_cache
        _analysis_cache["last_analysis_type"] = analysis_type
        _analysis_cache["last_analysis_data"] = analysis_data
        _analysis_cache["timestamp"] = datetime.now()
        logger.info(f"📝 Analysis saved to cache: {analysis_type}")

    def _get_analysis_from_cache(self):
        """Get analysis data from global cache."""
        global _analysis_cache

        # Check if cache is not too old (1 hour limit)
        if _analysis_cache["timestamp"]:
            time_diff = datetime.now() - _analysis_cache["timestamp"]
            if time_diff.total_seconds() > 3600:  # 1 hour
                logger.info("🕐 Cache expired, clearing analysis data")
                _analysis_cache = {
                    "last_analysis_type": None,
                    "last_analysis_data": None,
                    "timestamp": None,
                }
                return None, None

        return (
            _analysis_cache["last_analysis_type"],
            _analysis_cache["last_analysis_data"],
        )

    async def process_message(self, message: str) -> ChatResponse:
        """Process incoming chat message and return appropriate response."""
        message_lower = message.lower()
        logger.info(f"💬 Processing message: {message[:100]}...")

        try:
            # Handle email sending requests
            if any(
                keyword in message_lower
                for keyword in [
                    "enviar",
                    "envía",
                    "mandar",
                    "manda",
                    "email",
                    "correo",
                    "informe",
                    "reporte",
                    "send",
                    "mail",
                ]
            ) and ("@" in message or "correo" in message_lower):
                return await self._handle_email_request(message)

            # Handle add product commands
            elif any(
                keyword in message_lower
                for keyword in [
                    "añadir",
                    "agregar",
                    "crear producto",
                    "nuevo producto",
                    "add product",
                    "add item",
                    "añadir inventario",
                ]
            ):
                return await self._handle_add_product(message)

            # Handle simple inventory listing (more specific patterns first)
            elif any(
                keyword in message_lower
                for keyword in [
                    "ver inventario",
                    "que elementos",
                    "elementos hay",
                    "qué hay en",
                    "listar inventario",
                    "mostrar productos",
                    "list inventory",
                    "show inventory",
                ]
            ):
                return await self._handle_list_inventory()

            # Handle inventory analysis (less specific - should come after listing)
            elif any(
                keyword in message_lower
                for keyword in [
                    "análisis de inventario",
                    "analizar inventario",
                    "ejecuta",
                    "ejecutar",
                    "analysis",
                    "analyze",
                    "restock",
                    "run",
                ]
            ):
                return await self._handle_inventory_analysis()

            # Handle sales analysis
            elif any(
                keyword in message_lower
                for keyword in [
                    "ventas",
                    "ingresos",
                    "cliente",
                    "rendimiento",
                    "análisis de ventas",
                    "analizar",
                    "analiza",
                    "muéstrame",
                    "sales",
                    "revenue",
                    "customer",
                    "performance",
                    "analyze",
                    "show",
                ]
            ):
                return await self._handle_sales_analysis()

            # Handle edit inventory
            elif any(
                keyword in message_lower
                for keyword in [
                    "editar",
                    "modificar",
                    "actualizar",
                    "cambiar",
                    "edit",
                    "modify",
                    "update",
                    "change",
                    "producto",
                ]
            ) and any(
                keyword in message_lower
                for keyword in ["producto", "inventario", "product", "inventory"]
            ):
                return await self._handle_edit_inventory(message)

            # Default help response
            else:
                return self._get_help_response()

        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return ChatResponse(
                response=f"❌ Error procesando mensaje: {str(e)}",
                workflow_id="error-" + datetime.now().strftime("%Y%m%d-%H%M%S"),
            )

    async def _handle_add_product(self, message: str) -> ChatResponse:
        """Handle add product command."""
        try:
            logger.info(f"🔍 ADD_PRODUCT: Starting with message: {message}")

            # Parse product data from natural language
            product_data = self._parse_product_data(message)

            if not product_data:
                logger.warning(
                    "❌ ADD_PRODUCT: Failed to parse product data from message"
                )
                return ChatResponse(
                    response="❌ No pude extraer la información del producto. "
                    'Usa el formato: Añadir producto: Nombre "...", Precio $X, Cantidad Y',
                    workflow_id="add-product-error-"
                    + datetime.now().strftime("%Y%m%d-%H%M%S"),
                )

            logger.info(f"✅ ADD_PRODUCT: Parsed data: {product_data}")

            # Create ProductCreateRequest
            product_request = ProductCreateRequest(
                name=product_data.get("name", ""),
                description=product_data.get("description", ""),
                category=product_data.get("category", "Other"),
                price=float(product_data.get("price", 0)),
                quantity=int(product_data.get("quantity", 0)),
                sku=product_data.get("sku"),
                minimum_stock=product_data.get("minimum_stock"),
                maximum_stock=product_data.get("maximum_stock"),
                unit_cost=product_data.get("unit_cost"),
            )

            # Check for duplicates
            existing_products = await self.db_service.get_all_products()
            proposed_sku = (
                product_request.sku or f"SKU-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            )

            for existing_product in existing_products:
                if (
                    existing_product.name.lower().strip()
                    == product_request.name.lower().strip()
                ):
                    return ChatResponse(
                        response=f"❌ **Producto Duplicado**: Ya existe un producto con el nombre '{existing_product.name}'. "
                        "Los nombres de productos deben ser únicos.",
                        workflow_id="add-product-duplicate-"
                        + datetime.now().strftime("%Y%m%d-%H%M%S"),
                    )

                if existing_product.sku.upper() == proposed_sku.upper():
                    return ChatResponse(
                        response=f"❌ **SKU Duplicado**: Ya existe un producto con el SKU '{existing_product.sku}'. "
                        "Los SKUs deben ser únicos.",
                        workflow_id="add-product-sku-duplicate-"
                        + datetime.now().strftime("%Y%m%d-%H%M%S"),
                    )

            # Set the SKU
            product_request.sku = proposed_sku

            # Create the product
            product = await self.db_service.create_product(product_request)

            # Get inventory summary
            inventory_summary = await self.db_service.get_inventory_summary()

            response_text = f"""✅ **¡Producto Añadido al Inventario!**

**Detalles del Producto:**
- **Nombre:** {product.name}
- **SKU:** {product.sku}
- **Categoría:** {product.category}
- **Precio:** ${product.price:.2f}
- **Cantidad inicial:** {product_request.quantity} unidades
- **Stock mínimo:** {product_request.minimum_stock or max(5, product_request.quantity // 5)}
- **Stock máximo:** {product_request.maximum_stock or product_request.quantity * 2}

**Resumen del Inventario:**
- Total productos únicos: {inventory_summary["total_products"]}
- Total unidades en inventario: {inventory_summary["total_units"]}

¡El producto ha sido añadido exitosamente al sistema!"""

            logger.info("✅ ADD_PRODUCT: Completed successfully")

            return ChatResponse(
                response=response_text,
                data={
                    "product_id": product.id,
                    "product_name": product.name,
                    "product_sku": product.sku,
                    "inventory_summary": inventory_summary,
                },
                workflow_id=f"add-product-{product.id}",
            )

        except Exception as e:
            logger.error(f"Error in _handle_add_product: {str(e)}")
            return ChatResponse(
                response=f"❌ Error añadiendo producto: {str(e)}",
                workflow_id="add-product-error-"
                + datetime.now().strftime("%Y%m%d-%H%M%S"),
            )

    async def _handle_list_inventory(self) -> ChatResponse:
        """Handle inventory listing command."""
        try:
            logger.info("📋 LIST_INVENTORY: Starting inventory listing")

            products_with_stock = await self.db_service.get_products_with_stock()
            summary = await self.db_service.get_inventory_summary()

            if not products_with_stock:
                return ChatResponse(
                    response="📦 **Inventario Vacío**\n\nNo hay productos en el inventario actualmente. "
                    "Puedes añadir productos usando comandos como:\n"
                    "'Añadir producto: Laptop, precio $500, cantidad 10'",
                    workflow_id="list-inventory-empty-"
                    + datetime.now().strftime("%Y%m%d-%H%M%S"),
                )

            # Build inventory listing
            inventory_text = "📦 **Inventario Actual:**\n\n"

            # Group by status
            normal_items = [
                p for p in products_with_stock if p["stock_status"] == "normal"
            ]
            low_items = [p for p in products_with_stock if p["stock_status"] == "bajo"]
            critical_items = [
                p for p in products_with_stock if p["stock_status"] == "crítico"
            ]
            out_of_stock = [
                p for p in products_with_stock if p["stock_status"] == "agotado"
            ]

            # Normal stock items
            if normal_items:
                inventory_text += "✅ **Stock Normal:**\n"
                for item in normal_items[:5]:  # Limit to 5 items
                    inventory_text += f"- **{item['name']}** (SKU: {item['sku']}) - {item['stock_quantity']} unidades - ${item['price']:.2f}\n"
                if len(normal_items) > 5:
                    inventory_text += f"... y {len(normal_items) - 5} productos más\n"
                inventory_text += "\n"

            # Low stock items
            if low_items:
                inventory_text += "⚠️ **Stock Bajo:**\n"
                for item in low_items:
                    inventory_text += f"- **{item['name']}** - Solo {item['stock_quantity']} unidades restantes\n"
                inventory_text += "\n"

            # Critical stock items
            if critical_items:
                inventory_text += "🚨 **Stock Crítico:**\n"
                for item in critical_items:
                    inventory_text += f"- **{item['name']}** - ¡Solo {item['stock_quantity']} unidades!\n"
                inventory_text += "\n"

            # Out of stock items
            if out_of_stock:
                inventory_text += "❌ **Agotados:**\n"
                for item in out_of_stock:
                    inventory_text += f"- **{item['name']}** - Sin stock\n"
                inventory_text += "\n"

            # Summary
            inventory_text += f"""📊 **Resumen:**
- **Total productos:** {summary["total_products"]}
- **Total unidades:** {summary["total_units"]}
- **Productos con stock bajo:** {summary["low_stock_items"]}
- **Valor total estimado:** ${sum(p["price"] * p["stock_quantity"] for p in products_with_stock):.2f}"""

            return ChatResponse(
                response=inventory_text,
                data={
                    "products": products_with_stock,
                    "summary": summary,
                    "categories": {
                        "normal": len(normal_items),
                        "low": len(low_items),
                        "critical": len(critical_items),
                        "out_of_stock": len(out_of_stock),
                    },
                },
                workflow_id="list-inventory-"
                + datetime.now().strftime("%Y%m%d-%H%M%S"),
            )

        except Exception as e:
            logger.error(f"Error in _handle_list_inventory: {str(e)}")
            return ChatResponse(
                response=f"❌ Error obteniendo inventario: {str(e)}",
                workflow_id="list-inventory-error-"
                + datetime.now().strftime("%Y%m%d-%H%M%S"),
            )

    async def _handle_inventory_analysis(self) -> ChatResponse:
        """Handle inventory analysis command by delegating to InventoryAgent."""
        try:
            logger.info("📊 INVENTORY_ANALYSIS: Delegating to InventoryAgent")

            # Delegate all analysis to InventoryAgent
            result = await self.inventory_agent.analyze_inventory()

            if not result["success"]:
                return ChatResponse(
                    response=f"📊 **Análisis de Inventario**\n\n❌ {result['error']}. "
                    "Añade algunos productos primero.",
                    workflow_id=result.get(
                        "workflow_id",
                        "inventory-analysis-empty-"
                        + datetime.now().strftime("%Y%m%d-%H%M%S"),
                    ),
                )

            # Get analytics data for summary
            analytics_data = await self.db_service.get_analytics_data()
            summary = analytics_data["summary"]

            # Format data for email cache with proper structure
            email_data = {
                "analysis_type": "inventory",
                "summary": {
                    "total_items": summary.get("total_products", 0),
                    "total_units": summary.get("total_units", 0),
                    "total_value": result["analysis"]["total_value"],
                    "critical_items_count": result["analysis"]["low_stock_count"],
                    "analysis_date": result["analysis"]["analysis_date"],
                },
                "recommendations": result["analysis"]["recommendations"],
                "insights": result["text_report"],
                "charts": result["charts"],
                "categories": result["analysis"]["categories"],
                "top_products": result["analysis"]["top_products"],
            }

            # Save formatted data to cache
            self._save_analysis_to_cache("inventory", email_data)

            return ChatResponse(
                response=result["text_report"],
                charts=result["charts"],
                data=result["analysis"],
                workflow_id=result["workflow_id"],
            )

        except Exception as e:
            logger.error(f"Error in _handle_inventory_analysis: {str(e)}")
            return ChatResponse(
                response=f"❌ Error en análisis de inventario: {str(e)}",
                workflow_id="inventory-analysis-error-"
                + datetime.now().strftime("%Y%m%d-%H%M%S"),
            )

    async def _handle_sales_analysis(self) -> ChatResponse:
        """Handle sales analysis command."""
        try:
            logger.info("💰 SALES_ANALYSIS: Starting analysis")

            analytics_data = await self.db_service.get_analytics_data()
            orders = analytics_data["orders"]
            customers = analytics_data["customers"]

            if not orders:
                return ChatResponse(
                    response="💰 **Análisis de Ventas**\n\n❌ No hay datos de ventas disponibles. "
                    "Realiza algunas ventas primero.",
                    workflow_id="sales-analysis-empty-"
                    + datetime.now().strftime("%Y%m%d-%H%M%S"),
                )

            # Calculate sales statistics
            total_sales = sum(float(order["total_amount"]) for order in orders)
            total_orders = len(orders)
            average_order = total_sales / total_orders if total_orders > 0 else 0

            # Group by status
            status_counts = {}
            for order in orders:
                status = order["status"]
                status_counts[status] = status_counts.get(status, 0) + 1

            # Recent orders (last 5)
            recent_orders = sorted(
                orders, key=lambda x: x.get("order_date", ""), reverse=True
            )[:5]

            # BUILD SALES ANALYSIS TEXT
            sales_text = f"""💰 **Análisis Completo de Ventas**

**📈 Resumen de Ventas:**
- **Total órdenes:** {total_orders}
- **Ingresos totales:** ${total_sales:.2f}
- **Valor promedio por orden:** ${average_order:.2f}
- **Total clientes:** {len(customers)}

**📊 Estado de Órdenes:**
"""

            for status, count in status_counts.items():
                percentage = (count / total_orders) * 100
                sales_text += (
                    f"- **{status.title()}:** {count} órdenes ({percentage:.1f}%)\n"
                )

            sales_text += """
**🛒 Órdenes Recientes:**
"""

            for i, order in enumerate(recent_orders, 1):
                order_date = (
                    order.get("order_date", "")[:10]
                    if order.get("order_date")
                    else "N/A"
                )
                sales_text += f"{i}. **Orden #{order['id']}** - ${order['total_amount']:.2f} ({order_date})\n"

            # Customer analysis
            if customers:
                sales_text += f"""
**👥 Análisis de Clientes:**
- **Total clientes registrados:** {len(customers)}
- **Promedio de órdenes por cliente:** {total_orders / len(customers):.1f}
"""

            # GENERATE CHARTS
            charts = await self._generate_sales_charts(
                orders, customers, analytics_data
            )

            # Save to cache
            analysis_data = {
                "total_sales": total_sales,
                "total_orders": total_orders,
                "average_order": average_order,
                "status_counts": status_counts,
                "recent_orders": recent_orders,
                "total_customers": len(customers),
                "analysis_date": datetime.now().isoformat(),
            }
            self._save_analysis_to_cache("sales", analysis_data)

            return ChatResponse(
                response=sales_text,
                charts=charts,  # Add charts to response
                data=analysis_data,
                workflow_id="sales-analysis-"
                + datetime.now().strftime("%Y%m%d-%H%M%S"),
            )

        except Exception as e:
            logger.error(f"Error in _handle_sales_analysis: {str(e)}")
            return ChatResponse(
                response=f"❌ Error en análisis de ventas: {str(e)}",
                workflow_id="sales-analysis-error-"
                + datetime.now().strftime("%Y%m%d-%H%M%S"),
            )

    async def _generate_sales_charts(self, orders, customers, analytics_data):
        """Generate charts for sales analysis."""
        try:
            charts = []

            # 1. SALES TRENDS CHART (Line Chart)
            # Prepare daily sales data
            daily_sales = {}
            for order in orders:
                order_date = order.get("order_date", "")[:10]  # Get date only
                if order_date:
                    if order_date not in daily_sales:
                        daily_sales[order_date] = 0
                    daily_sales[order_date] += float(order["total_amount"])

            # Sort by date and prepare chart data
            sorted_dates = sorted(daily_sales.keys())
            trend_data = []
            for date in sorted_dates:
                trend_data.append(
                    {
                        "name": date,  # Frontend busca 'name' para el eje X
                        "ventas": daily_sales[date],
                    }
                )

            charts.append(
                {
                    "type": "line",
                    "title": "📈 Tendencias de Ventas Diarias",
                    "data": trend_data,
                    "summary": {
                        "total_dias": len(sorted_dates),
                        "promedio_ventas_diarias": (
                            round(sum(daily_sales.values()) / len(daily_sales), 2)
                            if daily_sales
                            else 0
                        ),
                        "mejor_dia": (
                            max(daily_sales.items(), key=lambda x: x[1])
                            if daily_sales
                            else None
                        ),
                    },
                }
            )

            # 2. MONTHLY SALES PREDICTION (Line Chart)
            # Simple prediction based on current trend
            if len(daily_sales) >= 7:  # Need at least a week of data
                recent_daily_avg = sum(list(daily_sales.values())[-7:]) / 7

                # Generate next 30 days prediction
                predictions = []
                last_date = (
                    max(sorted_dates)
                    if sorted_dates
                    else datetime.now().strftime("%Y-%m-%d")
                )
                last_date_obj = datetime.strptime(last_date, "%Y-%m-%d")

                for i in range(1, 31):  # Next 30 days
                    future_date = last_date_obj + timedelta(days=i)
                    # Add some variation to make it realistic
                    predicted_value = recent_daily_avg * (
                        0.9 + (i % 7) * 0.02
                    )  # Weekly pattern
                    predictions.append(
                        {
                            "name": future_date.strftime(
                                "%Y-%m-%d"
                            ),  # Frontend busca 'name' para el eje X
                            "prediccion": round(predicted_value, 2),
                            "confianza": max(90 - i, 60),  # Decreasing confidence
                        }
                    )

                charts.append(
                    {
                        "type": "line",
                        "title": "🔮 Predicción de Ventas (30 días)",
                        "data": predictions,
                        "summary": {
                            "dias_prediccion": 30,
                            "promedio_predicho_diario": round(recent_daily_avg, 2),
                            "total_predicho": round(
                                sum(p["prediccion"] for p in predictions), 2
                            ),
                            "rango_confianza": "60-90%",
                        },
                    }
                )

            # 3. TOP PRODUCTS BY REVENUE (Bar Chart) - Con labels corregidos
            product_revenue = {}
            for order in orders:
                # For now, simulate product data from order info
                product_name = f"Producto #{order.get('id', 'N/A')}"
                if product_name not in product_revenue:
                    product_revenue[product_name] = 0
                product_revenue[product_name] += float(order["total_amount"])

            # Get top 5 products
            top_products = sorted(
                product_revenue.items(), key=lambda x: x[1], reverse=True
            )[:5]
            product_data = []
            for product, revenue in top_products:
                # Truncar nombre del producto para mejor visualización
                short_name = product if len(product) <= 12 else product[:12] + "..."
                product_data.append(
                    {
                        "name": short_name,  # Frontend busca 'name' para el eje X
                        "ingresos": round(revenue, 2),
                    }
                )

            if product_data:
                charts.append(
                    {
                        "type": "bar",
                        "title": "🏆 Top Productos por Ingresos",
                        "data": product_data,
                        "summary": {
                            "productos_top": len(product_data),
                            "mejor_producto": (
                                product_data[0]["name"] if product_data else "N/A"
                            ),
                            "ingresos_top5": round(
                                sum(p["ingresos"] for p in product_data), 2
                            ),
                        },
                    }
                )

            logger.info(f"📊 Generated {len(charts)} sales charts")
            return charts

        except Exception as e:
            logger.error(f"Error generating sales charts: {str(e)}")
            return []

    async def _handle_edit_inventory(self, message: str) -> ChatResponse:
        """Handle edit inventory command."""
        try:
            logger.info(f"✏️ EDIT_INVENTORY: Starting with message: {message}")

            # Parse edit data from natural language
            edit_data = self._parse_edit_data(message)

            if not edit_data:
                return ChatResponse(
                    response="❌ No pude extraer la información de edición. "
                    "Usa el formato: Editar producto ID X, cambiar precio a $Y, cantidad a Z",
                    workflow_id="edit-inventory-error-"
                    + datetime.now().strftime("%Y%m%d-%H%M%S"),
                )

            # Create ProductEditRequest
            product_edit = ProductEditRequest(
                product_id=edit_data.get("product_id"),
                name=edit_data.get("name"),
                price=edit_data.get("price"),
                category=edit_data.get("category"),
                description=edit_data.get("description"),
                quantity=edit_data.get("quantity"),
                minimum_stock=edit_data.get("minimum_stock"),
                maximum_stock=edit_data.get("maximum_stock"),
            )

            # Check if product exists
            existing_product = await self.db_service.get_product_by_id(
                product_edit.product_id
            )
            if not existing_product:
                return ChatResponse(
                    response=f"❌ **Producto no encontrado**: No existe un producto con ID {product_edit.product_id}",
                    workflow_id="edit-inventory-not-found-"
                    + datetime.now().strftime("%Y%m%d-%H%M%S"),
                )

            # Update the product
            updated_product = await self.db_service.update_product(
                product_edit.product_id, product_edit
            )
            if not updated_product:
                return ChatResponse(
                    response="❌ Error actualizando el producto",
                    workflow_id="edit-inventory-error-"
                    + datetime.now().strftime("%Y%m%d-%H%M%S"),
                )

            # Build response
            changes = []
            if edit_data.get("name"):
                changes.append(f"Nombre: {edit_data['name']}")
            if edit_data.get("price"):
                changes.append(f"Precio: ${edit_data['price']:.2f}")
            if edit_data.get("quantity") is not None:
                changes.append(f"Cantidad: {edit_data['quantity']}")

            changes_text = "**Cambios realizados:**\n" + "\n".join(
                f"- {change}" for change in changes
            )

            current_inventory = (
                updated_product.inventory_items[0]
                if updated_product.inventory_items
                else None
            )

            response_text = f"""✅ **¡Producto Editado Exitosamente!**

**Producto:** {updated_product.name}
**SKU:** {updated_product.sku}

{changes_text}

**Estado actual:** {current_inventory.status if current_inventory else "sin_inventario"}
**Stock actual:** {current_inventory.quantity if current_inventory else 0} unidades

¡La información del producto ha sido actualizada correctamente!"""

            return ChatResponse(
                response=response_text,
                data={
                    "product_id": updated_product.id,
                    "product_name": updated_product.name,
                    "changes": edit_data,
                    "current_stock": (
                        current_inventory.quantity if current_inventory else 0
                    ),
                },
                workflow_id=f"edit-inventory-{updated_product.id}",
            )

        except Exception as e:
            logger.error(f"Error in _handle_edit_inventory: {str(e)}")
            return ChatResponse(
                response=f"❌ Error editando inventario: {str(e)}",
                workflow_id="edit-inventory-error-"
                + datetime.now().strftime("%Y%m%d-%H%M%S"),
            )

    def _parse_product_data(self, message: str) -> Dict[str, Any]:
        """Parse product data from natural language message."""
        product_data = {}

        # Extract name (between quotes or after "producto:")
        name_match = re.search(
            r'(?:producto[:\s]+|nombre[:\s]+)["\']([^"\']+)["\']|(?:producto[:\s]+|nombre[:\s]+)([^,\n]+)',
            message,
            re.IGNORECASE,
        )
        if name_match:
            product_data["name"] = (name_match.group(1) or name_match.group(2)).strip()

        # Extract price
        price_match = re.search(
            r"precio[:\s]*\$?(\d+(?:\.\d{2})?)", message, re.IGNORECASE
        )
        if price_match:
            product_data["price"] = float(price_match.group(1))

        # Extract quantity
        quantity_match = re.search(r"cantidad[:\s]*(\d+)", message, re.IGNORECASE)
        if quantity_match:
            product_data["quantity"] = int(quantity_match.group(1))

        # Extract category (map Spanish to English)
        category_match = re.search(r"categoría[:\s]*([^,\n]+)", message, re.IGNORECASE)
        if category_match:
            category_spanish = category_match.group(1).strip().lower()
            product_data["category"] = self.category_mapping.get(
                category_spanish, category_spanish.title()
            )

        # Extract description
        desc_match = re.search(r"descripción[:\s]*([^,\n]+)", message, re.IGNORECASE)
        if desc_match:
            product_data["description"] = desc_match.group(1).strip()

        return product_data if product_data.get("name") else None

    def _parse_edit_data(self, message: str) -> Dict[str, Any]:
        """Parse edit data from natural language message."""
        edit_data = {}

        # Extract product ID
        id_match = re.search(r"(?:producto|id)[:\s]*(\d+)", message, re.IGNORECASE)
        if id_match:
            edit_data["product_id"] = int(id_match.group(1))

        # Extract new name
        name_match = re.search(
            r'nombre[:\s]*["\']([^"\']+)["\']|nombre[:\s]*([^,\n]+)',
            message,
            re.IGNORECASE,
        )
        if name_match:
            edit_data["name"] = (name_match.group(1) or name_match.group(2)).strip()

        # Extract new price
        price_match = re.search(
            r"precio[:\s]*\$?(\d+(?:\.\d{2})?)", message, re.IGNORECASE
        )
        if price_match:
            edit_data["price"] = float(price_match.group(1))

        # Extract new quantity
        quantity_match = re.search(r"cantidad[:\s]*(\d+)", message, re.IGNORECASE)
        if quantity_match:
            edit_data["quantity"] = int(quantity_match.group(1))

        return edit_data if edit_data.get("product_id") else None

    def _get_help_response(self) -> ChatResponse:
        """Return help response with available commands."""
        help_text = """🤖 **Asistente de Inventario y Ventas**

**Comandos disponibles:**

📦 **Gestión de Inventario:**
- *"Añadir producto: Laptop, precio $500, cantidad 10"*
- *"Ver inventario"* o *"Mostrar productos"*
- *"Editar producto ID 1, cambiar precio a $600"*
- *"Análisis de inventario"*

💰 **Análisis de Ventas:**
- *"Análisis de ventas"* o *"Mostrar ingresos"*
- *"Rendimiento de cliente"*

✨ **Ejemplos de uso:**
- *"Agregar producto: Televisor Samsung, precio $800, cantidad 5, categoría electrónicos"*
- *"Qué elementos hay en el inventario?"*
- *"Ejecutar análisis completo"*

¡Pregúntame lo que necesites sobre tu inventario y ventas!"""

        return ChatResponse(
            response=help_text,
            workflow_id="help-" + datetime.now().strftime("%Y%m%d-%H%M%S"),
        )

    async def _handle_email_request(self, message: str) -> ChatResponse:
        """Handle email sending requests."""
        try:
            logger.info(f"📧 EMAIL_REQUEST: Processing message: {message}")

            # Extract email address
            email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
            email_matches = re.findall(email_pattern, message)

            if not email_matches:
                return ChatResponse(
                    response="❌ No pude encontrar una dirección de email válida en tu mensaje. "
                    "Por favor incluye el email destino (ej: usuario@ejemplo.com)",
                    workflow_id="email-error-"
                    + datetime.now().strftime("%Y%m%d-%H%M%S"),
                )

            recipient_email = email_matches[0]

            # Get analysis data from cache
            last_analysis_type, last_analysis_data = self._get_analysis_from_cache()

            # Check if we have a recent analysis to send
            if not last_analysis_type or not last_analysis_data:
                return ChatResponse(
                    response="❌ No hay análisis reciente para enviar. "
                    "Primero solicita un análisis de ventas o inventario, luego podrás enviarlo por email.",
                    workflow_id="email-no-analysis-"
                    + datetime.now().strftime("%Y%m%d-%H%M%S"),
                )

            # Determine report type and regenerate charts
            if last_analysis_type == "sales":
                report_type = "Análisis de Ventas"
                charts = await self._regenerate_sales_charts()
                summary = f"Análisis de ventas - Total: ${last_analysis_data.get('total_sales', 0):,.2f}, Órdenes: {last_analysis_data.get('total_orders', 0)}"
            elif last_analysis_type == "inventory":
                report_type = "Análisis de Inventario"
                charts = await self._regenerate_inventory_charts()
                summary = "Análisis completo del estado actual del inventario"
            else:
                return ChatResponse(
                    response="❌ Tipo de análisis no reconocido para envío por email.",
                    workflow_id="email-unknown-type-"
                    + datetime.now().strftime("%Y%m%d-%H%M%S"),
                )

            # Send email with complete analysis data
            success = send_analysis_report(
                recipient_email=recipient_email,
                report_type=report_type,
                charts=charts,
                summary=summary,
                analysis_data=last_analysis_data,
            )

            if success:
                return ChatResponse(
                    response=f"✅ **Reporte enviado exitosamente** 📧\n\n"
                    f"**Destinatario:** {recipient_email}\n"
                    f"**Tipo:** {report_type}\n"
                    f"**Gráficas incluidas:** {len(charts)}\n\n"
                    f"El reporte ha sido enviado con todas las gráficas del análisis.",
                    workflow_id="email-sent-"
                    + datetime.now().strftime("%Y%m%d-%H%M%S"),
                )
            else:
                return ChatResponse(
                    response="❌ **Error al enviar el reporte**\n\n"
                    "Verifica que las credenciales de email estén configuradas correctamente. "
                    "Consulta el archivo EMAIL_SETUP.md para más información.",
                    workflow_id="email-failed-"
                    + datetime.now().strftime("%Y%m%d-%H%M%S"),
                )

        except Exception as e:
            logger.error(f"Error handling email request: {str(e)}")
            return ChatResponse(
                response=f"❌ Error procesando solicitud de email: {str(e)}",
                workflow_id="email-error-" + datetime.now().strftime("%Y%m%d-%H%M%S"),
            )

    async def _regenerate_sales_charts(self) -> list:
        """Regenerate sales charts for email sending."""
        try:
            # Get fresh data
            orders = await self.db_service.get_all_orders()
            customers = await self.db_service.get_all_customers()
            analytics_data = await self.db_service.get_analytics_data()

            # Generate charts metadata (same logic as in _handle_sales_analysis)
            charts_metadata = await self._generate_sales_charts(
                orders, customers, analytics_data
            )

            # Generate actual base64 images from metadata
            email_charts = []
            chart_names = [
                "Ventas por Período",
                "Ventas por Cliente",
                "Top Productos Vendidos",
                "Ingresos Totales",
                "Tendencias de Ventas",
            ]

            for i, chart_metadata in enumerate(charts_metadata):
                chart_name = (
                    chart_names[i] if i < len(chart_names) else f"Gráfica {i+1}"
                )

                # Generate base64 image from metadata
                base64_image = await self._generate_chart_image(chart_metadata)

                if base64_image:
                    email_charts.append(
                        {
                            "name": chart_name,
                            "data": base64_image,
                        }
                    )

            return email_charts

        except Exception as e:
            logger.error(f"Error regenerating sales charts: {str(e)}")
            return []

    async def _regenerate_inventory_charts(self) -> list:
        """Regenerate inventory charts for email sending."""
        try:
            # Get fresh inventory data
            result = await self.inventory_agent.analyze_inventory()

            # Extract charts from the result (these are metadata, not images)
            charts_metadata = result.get("charts", [])

            # Generate actual base64 images from metadata
            email_charts = []
            chart_names = [
                "Estados de Stock",
                "Categorías por Valor",
                "Distribución de Cantidades",
                "Productos más Valiosos",
                "Urgencia de Restock",
            ]

            for i, chart_metadata in enumerate(charts_metadata):
                chart_name = (
                    chart_names[i] if i < len(chart_names) else f"Gráfica {i+1}"
                )

                # Generate base64 image from metadata
                base64_image = await self._generate_chart_image(chart_metadata)

                if base64_image:
                    email_charts.append(
                        {
                            "name": chart_name,
                            "data": base64_image,
                        }
                    )

            return email_charts

        except Exception as e:
            logger.error(f"Error regenerating inventory charts: {str(e)}")
            return []

    async def _generate_chart_image(self, chart_metadata: Dict) -> str:
        """Generate base64 image from chart metadata."""
        try:
            import matplotlib.pyplot as plt
            import matplotlib.patches as mpatches
            from io import BytesIO
            import base64

            # Set up the figure
            plt.style.use("default")
            fig, ax = plt.subplots(figsize=(10, 6))
            fig.patch.set_facecolor("white")

            chart_type = chart_metadata.get("type", "bar")
            data = chart_metadata.get("data", [])
            title = chart_metadata.get("title", "Gráfica")

            if not data:
                return ""

            if chart_type == "pie":
                # PIE CHART
                labels = [item.get("name", "") for item in data]
                values = [item.get("value", 0) for item in data]
                colors = [item.get("color", "#3B82F6") for item in data]

                wedges, texts, autotexts = ax.pie(
                    values,
                    labels=labels,
                    colors=colors,
                    autopct="%1.1f%%",
                    startangle=90,
                )

                # Improve text formatting
                for autotext in autotexts:
                    autotext.set_color("white")
                    autotext.set_fontweight("bold")

            elif chart_type == "bar":
                # BAR CHART
                labels = [item.get("name", "") for item in data]

                # Find the first numeric field for values
                value_key = None
                for key in data[0].keys() if data else []:
                    if key != "name" and isinstance(data[0].get(key), (int, float)):
                        value_key = key
                        break

                if value_key:
                    values = [item.get(value_key, 0) for item in data]
                    bars = ax.bar(labels, values, color="#3B82F6", alpha=0.8)

                    # Add value labels on bars
                    for bar, value in zip(bars, values):
                        height = bar.get_height()
                        ax.text(
                            bar.get_x() + bar.get_width() / 2.0,
                            height + max(values) * 0.01,
                            f"{value:,.0f}",
                            ha="center",
                            va="bottom",
                            fontweight="bold",
                        )

                    ax.set_ylabel(value_key.title())

                    # Rotate x-axis labels if they're long
                    if any(len(label) > 10 for label in labels):
                        plt.xticks(rotation=45, ha="right")

            elif chart_type == "line":
                # LINE CHART
                labels = [item.get("name", "") for item in data]

                # Find the first numeric field for values
                value_key = None
                for key in data[0].keys() if data else []:
                    if key != "name" and isinstance(data[0].get(key), (int, float)):
                        value_key = key
                        break

                if value_key:
                    values = [item.get(value_key, 0) for item in data]

                    # Create line plot
                    ax.plot(
                        labels,
                        values,
                        color="#3B82F6",
                        marker="o",
                        linewidth=2,
                        markersize=6,
                    )

                    # Add value labels on points
                    for i, (label, value) in enumerate(zip(labels, values)):
                        ax.annotate(
                            f"{value:,.0f}",
                            (i, value),
                            textcoords="offset points",
                            xytext=(0, 10),
                            ha="center",
                            fontweight="bold",
                            fontsize=8,
                        )

                    ax.set_ylabel(value_key.title())
                    ax.set_xlabel("Fecha")

                    # Rotate x-axis labels for better readability
                    plt.xticks(rotation=45, ha="right")

            # Set title and styling
            ax.set_title(title, fontsize=14, fontweight="bold", pad=20)
            ax.grid(True, alpha=0.3)

            # Improve layout
            plt.tight_layout()

            # Convert to base64
            buffer = BytesIO()
            plt.savefig(
                buffer,
                format="png",
                dpi=150,
                bbox_inches="tight",
                facecolor="white",
                edgecolor="none",
            )
            buffer.seek(0)

            image_base64 = base64.b64encode(buffer.read()).decode("utf-8")
            plt.close(fig)  # Clean up

            return f"data:image/png;base64,{image_base64}"

        except Exception as e:
            logger.error(f"Error generating chart image: {str(e)}")
            return ""
