"""
Chat Service for processing natural language commands - Database Version.
"""

import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

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

            # Handle add product commands (check for specific add patterns)
            elif any(
                keyword in message_lower
                for keyword in [
                    "añadir",
                    "añade",
                    "agregar",
                    "agrega",
                    "crear producto",
                    "nuevo producto",
                    "add product",
                    "add item",
                    "añadir inventario",
                ]
            ) or (
                # Also detect patterns like "Añade el producto X con..."
                re.search(
                    r"(?:añade|añadir|agregar|agrega|crear)\s+(?:el\s+)?producto",
                    message_lower,
                )
            ):
                return await self._handle_add_product(message)

            # Handle create sale/order commands (HIGHER PRIORITY - check first)
            elif any(
                keyword in message_lower
                for keyword in [
                    "vender",
                    "crear venta",
                    "nueva venta",
                    "nueva orden",
                    "crear orden",
                    "sell",
                    "create sale",
                    "new sale",
                    "new order",
                    "create order",
                ]
            ) or (
                # Also detect patterns like "2 Laptops, 1 TV a cliente"
                re.search(r"\d+\s+\w+.*a\s+cliente", message_lower)
                or re.search(r"vender\s+\d+", message_lower)
            ):
                return await self._handle_create_sale(message)

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
                    "rendimiento",
                    "análisis de ventas",
                    "analizar ventas",
                    "analiza ventas",
                    "muéstrame ventas",
                    "sales",
                    "revenue",
                    "performance",
                    "sales analysis",
                    "show sales",
                ]
            ):
                return await self._handle_sales_analysis()

            # Handle edit inventory (exclude add commands)
            elif (
                any(
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
                    ]
                )
                and any(
                    keyword in message_lower
                    for keyword in ["producto", "inventario", "product", "inventory"]
                )
            ) and not any(
                # Exclude add commands
                keyword in message_lower
                for keyword in [
                    "añadir",
                    "añade",
                    "agregar",
                    "agrega",
                    "crear",
                    "nuevo",
                ]
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

            # Transform summary to match frontend expectations
            frontend_summary = {
                "total_items": summary.get("total_products", 0),
                "critical_items_count": len(
                    critical_items
                ),  # Use actual critical count
                "low_stock_items_count": len(low_items),  # Use actual low stock count
                "recommendations_count": 0,  # Default for listing
                "charts_generated": 0,  # Default for listing
                "ai_interactions": 0,  # Default for listing
                "tools_used": ["list_inventory"],
            }

            return ChatResponse(
                response=inventory_text,
                data={
                    "products": products_with_stock,
                    "summary": frontend_summary,
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
                # Handle both dict (from analytics_data) and SQLAlchemy object (from get_all_orders)
                if isinstance(order, dict):
                    order_date = (
                        order.get("order_date", "")[:10]
                        if order.get("order_date")
                        else ""
                    )
                    total_amount = order["total_amount"]
                else:
                    order_date = str(order.order_date)[:10] if order.order_date else ""
                    total_amount = order.total_amount

                if order_date:
                    if order_date not in daily_sales:
                        daily_sales[order_date] = 0
                    daily_sales[order_date] += float(total_amount)

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

            # 3. TOP PRODUCTS BY REVENUE (Bar Chart) - Con nombres reales de productos
            product_revenue = {}

            # Get real product data from order_items
            for order in orders:
                # Handle both dict and SQLAlchemy object
                if isinstance(order, dict):
                    order_items = order.get(
                        "items", []
                    )  # From analytics_data uses "items"
                else:
                    order_items = (
                        order.order_items if hasattr(order, "order_items") else []
                    )

                # Process each item in the order
                for item in order_items:
                    if isinstance(item, dict):
                        product_name = item.get(
                            "product_name", f"Producto #{item.get('product_id', 'N/A')}"
                        )
                        total_price = item.get("total_price", 0)
                    else:
                        # For SQLAlchemy objects, get product name from relationship
                        product_name = (
                            item.product.name
                            if hasattr(item, "product") and item.product
                            else f"Producto #{item.product_id if hasattr(item, 'product_id') else 'N/A'}"
                        )
                        total_price = (
                            item.total_price if hasattr(item, "total_price") else 0
                        )

                    if product_name not in product_revenue:
                        product_revenue[product_name] = 0
                    product_revenue[product_name] += float(total_price)

            # If no product data found, fall back to order-based grouping
            if not product_revenue:
                for order in orders:
                    if isinstance(order, dict):
                        order_id = order.get("id", "N/A")
                        total_amount = order["total_amount"]
                    else:
                        order_id = order.id if order.id else "N/A"
                        total_amount = order.total_amount

                    product_name = f"Orden #{order_id}"
                    if product_name not in product_revenue:
                        product_revenue[product_name] = 0
                    product_revenue[product_name] += float(total_amount)

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
                    "Puedes usar comandos como:\n"
                    "• 'Actualizar Vajilla de porcelana a 15 productos'\n"
                    "• 'Actualizar Vajilla de porcelana precio a 1500'\n"
                    "• 'Editar producto ID 1, cambiar precio a $600'",
                    workflow_id="edit-inventory-error-"
                    + datetime.now().strftime("%Y%m%d-%H%M%S"),
                )

            # Find the product (by ID or by name search)
            existing_product = None
            product_id = edit_data.get("product_id")

            if product_id:
                # Search by ID (traditional method)
                existing_product = await self.db_service.get_product_by_id(product_id)
                if not existing_product:
                    return ChatResponse(
                        response=f"❌ **Producto no encontrado**: No existe un producto con ID {product_id}",
                        workflow_id="edit-inventory-not-found-"
                        + datetime.now().strftime("%Y%m%d-%H%M%S"),
                    )
            elif edit_data.get("search_name"):
                # Search by name (new flexible method)
                search_name = edit_data.get("search_name").lower()
                all_products = await self.db_service.get_all_products()

                # Find exact or partial matches
                matches = []
                for product in all_products:
                    if search_name in product.name.lower():
                        matches.append(product)

                if not matches:
                    return ChatResponse(
                        response=f"❌ **Producto no encontrado**: No encontré ningún producto que contenga '{edit_data.get('search_name')}'.\n"
                        "Verifica el nombre o usa 'Ver inventario' para ver todos los productos disponibles.",
                        workflow_id="edit-inventory-not-found-"
                        + datetime.now().strftime("%Y%m%d-%H%M%S"),
                    )
                elif len(matches) > 1:
                    # Multiple matches - show options
                    options = "\n".join([f"• ID {p.id}: {p.name}" for p in matches[:5]])
                    return ChatResponse(
                        response=f"❓ **Múltiples productos encontrados** para '{edit_data.get('search_name')}':\n\n{options}\n\n"
                        "Por favor especifica el ID del producto que quieres editar.",
                        workflow_id="edit-inventory-multiple-"
                        + datetime.now().strftime("%Y%m%d-%H%M%S"),
                    )
                else:
                    # Single match found
                    existing_product = matches[0]
                    product_id = existing_product.id

            if not existing_product:
                return ChatResponse(
                    response="❌ **Error**: No se pudo identificar el producto a editar.",
                    workflow_id="edit-inventory-error-"
                    + datetime.now().strftime("%Y%m%d-%H%M%S"),
                )

            # Create ProductEditRequest
            product_edit = ProductEditRequest(
                product_id=product_id,
                name=edit_data.get("name"),
                price=edit_data.get("price"),
                category=edit_data.get("category"),
                description=edit_data.get("description"),
                quantity=edit_data.get("quantity"),
                minimum_stock=edit_data.get("minimum_stock"),
                maximum_stock=edit_data.get("maximum_stock"),
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

    async def _handle_create_sale(self, message: str) -> ChatResponse:
        """Handle create sale command with multiple products support."""
        try:
            logger.info(f"🛒 CREATE_SALE: Starting with message: {message}")

            # Parse sale data from natural language
            sale_data = self._parse_sale_data(message)

            if not sale_data:
                return ChatResponse(
                    response="❌ No pude extraer la información de la venta. "
                    "Puedes usar comandos como:\n"
                    "• 'Vender 3 unidades de TV, 4 de vajilla a cliente Andres'\n"
                    "• 'Crear venta: Cliente ID 1, Producto Laptop cantidad 2'\n"
                    "• 'Nueva orden: Cliente Juan, Televisor x1, Laptop x2'",
                    workflow_id="create-sale-error-"
                    + datetime.now().strftime("%Y%m%d-%H%M%S"),
                )

            # Find or create customer
            customer_id = await self._resolve_customer(sale_data.get("customer"))
            if not customer_id:
                return ChatResponse(
                    response="❌ **Error con el cliente**: No pude identificar o crear el cliente especificado.",
                    workflow_id="create-sale-customer-error-"
                    + datetime.now().strftime("%Y%m%d-%H%M%S"),
                )

            # Resolve products and validate stock
            resolved_items = []
            stock_errors = []

            for item in sale_data.get("items", []):
                product_name = item.get("product_name")
                quantity = item.get("quantity")

                # Find product by name
                all_products = await self.db_service.get_all_products()
                matching_products = []

                for product in all_products:
                    if (
                        product_name.lower() in product.name.lower()
                        or product.name.lower() in product_name.lower()
                    ):
                        matching_products.append(product)

                if not matching_products:
                    stock_errors.append(f"❌ Producto '{product_name}' no encontrado")
                    continue
                elif len(matching_products) > 1:
                    # Multiple matches - use the best match
                    best_match = min(matching_products, key=lambda p: len(p.name))
                    product = best_match
                else:
                    product = matching_products[0]

                # Check stock availability
                if not product.inventory_items:
                    stock_errors.append(
                        f"❌ '{product.name}': Sin inventario disponible"
                    )
                    continue

                current_stock = product.inventory_items[0].quantity
                if current_stock < quantity:
                    stock_errors.append(
                        f"❌ '{product.name}': Stock insuficiente. "
                        f"Disponible: {current_stock}, Solicitado: {quantity}"
                    )
                    continue

                # Add to resolved items
                resolved_items.append(
                    {
                        "product_id": product.id,
                        "quantity": quantity,
                        "price": float(product.price),
                    }
                )

            # If there are stock errors, return them
            if stock_errors:
                error_message = "❌ **Errores en la venta:**\n\n" + "\n".join(
                    stock_errors
                )
                if resolved_items:
                    error_message += "\n\n💡 **Productos disponibles:**\n"
                    for item in resolved_items:
                        product = await self.db_service.get_product_by_id(
                            item["product_id"]
                        )
                        error_message += f"• {product.name}: {item['quantity']} unidades disponibles\n"

                return ChatResponse(
                    response=error_message,
                    workflow_id="create-sale-stock-error-"
                    + datetime.now().strftime("%Y%m%d-%H%M%S"),
                )

            if not resolved_items:
                return ChatResponse(
                    response="❌ **Error**: No se pudieron procesar los productos solicitados.",
                    workflow_id="create-sale-no-items-"
                    + datetime.now().strftime("%Y%m%d-%H%M%S"),
                )

            # Create the order
            order = await self.db_service.create_order(
                customer_id=customer_id,
                items=resolved_items,
                payment_method=sale_data.get("payment_method", "credit_card"),
            )

            # Build success response
            customer = await self.db_service.get_customer_by_id(customer_id)

            # Get updated product info for response
            items_text = ""
            total_items = 0
            for item in resolved_items:
                product = await self.db_service.get_product_by_id(item["product_id"])
                updated_stock = (
                    product.inventory_items[0].quantity
                    if product.inventory_items
                    else 0
                )
                items_text += f"• **{product.name}**: {item['quantity']} unidades × ${item['price']:.2f} = ${item['quantity'] * item['price']:.2f}\n"
                items_text += f"  _(Stock restante: {updated_stock} unidades)_\n"
                total_items += item["quantity"]

            response_text = f"""✅ **¡Venta Creada Exitosamente!** 🎉

**📋 Detalles de la Orden:**
- **ID de Orden:** #{order.id}
- **Cliente:** {customer.name}
- **Total de productos:** {total_items} unidades
- **Monto total:** ${order.total_amount:.2f}
- **Estado:** {order.status}

**🛍️ Productos vendidos:**
{items_text}

**💳 Método de pago:** {order.payment_method}
**📅 Fecha:** {order.order_date.strftime('%Y-%m-%d %H:%M') if order.order_date else 'N/A'}

¡El inventario ha sido actualizado automáticamente!"""

            return ChatResponse(
                response=response_text,
                data={
                    "order_id": order.id,
                    "customer_id": customer_id,
                    "customer_name": customer.name,
                    "total_amount": float(order.total_amount),
                    "items_count": len(resolved_items),
                    "total_units": total_items,
                    "items": resolved_items,
                },
                workflow_id=f"create-sale-{order.id}",
            )

        except Exception as e:
            logger.error(f"Error in _handle_create_sale: {str(e)}")
            return ChatResponse(
                response=f"❌ Error creando venta: {str(e)}",
                workflow_id="create-sale-error-"
                + datetime.now().strftime("%Y%m%d-%H%M%S"),
            )

    def _parse_product_data(self, message: str) -> Dict[str, Any]:
        """Parse product data from natural language message with flexible patterns."""
        product_data = {}

        # Extract name with multiple flexible patterns
        name_patterns = [
            # Traditional patterns
            r'(?:producto[:\s]+|nombre[:\s]+)["\']([^"\']+)["\']',  # "producto: 'Lija'"
            r"(?:producto[:\s]+|nombre[:\s]+)([^,\n]+)",  # "producto: Lija"
            # Natural language patterns
            r"(?:añade|añadir|agregar|crear)\s+(?:el\s+)?producto\s+([^,\s]+)",  # "Añade el producto Lija"
            r"(?:añade|añadir|agregar|crear)\s+([^,\s]+)\s+con",  # "Añade Lija con"
            r"producto\s+([^,\s]+)\s+(?:con|precio|valor)",  # "producto Lija con"
            r"nuevo\s+producto[:\s]*([^,\n]+)",  # "nuevo producto: Lija"
        ]

        for pattern in name_patterns:
            name_match = re.search(pattern, message, re.IGNORECASE)
            if name_match:
                product_name = name_match.group(1).strip()
                # Clean up common words
                product_name = re.sub(
                    r"\s+(con|y|de|precio|valor|cantidad).*$",
                    "",
                    product_name,
                    flags=re.IGNORECASE,
                )
                if product_name:
                    product_data["name"] = product_name
                    break

        # Extract price with multiple patterns
        price_patterns = [
            r"precio[:\s]*\$?(\d+(?:\.\d{2})?)",  # "precio $500"
            r"valor[:\s]*(?:de[:\s]*)?\$?(\d+(?:\.\d{2})?)",  # "valor de 500"
            r"cuesta[:\s]*\$?(\d+(?:\.\d{2})?)",  # "cuesta $500"
            r"con\s+(?:valor|precio)\s+(?:de\s+)?\$?(\d+(?:\.\d{2})?)",  # "con valor de 500"
            r"\$(\d+(?:\.\d{2})?)",  # "$500"
        ]

        for pattern in price_patterns:
            price_match = re.search(pattern, message, re.IGNORECASE)
            if price_match:
                product_data["price"] = float(price_match.group(1))
                break

        # Extract quantity with multiple patterns
        quantity_patterns = [
            r"cantidad[:\s]*(\d+)",  # "cantidad 20"
            r"(\d+)\s+unidades?",  # "20 unidades"
            r"y\s+(\d+)\s+unidades?",  # "y 20 unidades"
            r"con\s+(\d+)\s+unidades?",  # "con 20 unidades"
            r"stock[:\s]*(\d+)",  # "stock 20"
            r"inventario[:\s]*(\d+)",  # "inventario 20"
        ]

        for pattern in quantity_patterns:
            quantity_match = re.search(pattern, message, re.IGNORECASE)
            if quantity_match:
                product_data["quantity"] = int(quantity_match.group(1))
                break

        # Extract category (map Spanish to English)
        category_patterns = [
            r"categoría[:\s]*([^,\n]+)",  # "categoría electrónicos"
            r"tipo[:\s]*([^,\n]+)",  # "tipo electrónicos"
            r"es\s+(?:un|una)\s+([^,\n]+)",  # "es un electrónico"
        ]

        for pattern in category_patterns:
            category_match = re.search(pattern, message, re.IGNORECASE)
            if category_match:
                category_spanish = category_match.group(1).strip().lower()
                product_data["category"] = self.category_mapping.get(
                    category_spanish, category_spanish.title()
                )
                break

        # Extract description
        desc_patterns = [
            r"descripción[:\s]*([^,\n]+)",  # "descripción: ..."
            r"describe[:\s]*([^,\n]+)",  # "describe: ..."
        ]

        for pattern in desc_patterns:
            desc_match = re.search(pattern, message, re.IGNORECASE)
            if desc_match:
                product_data["description"] = desc_match.group(1).strip()
                break

        return product_data if product_data.get("name") else None

    def _parse_edit_data(self, message: str) -> Dict[str, Any]:
        """Parse edit data from natural language message with flexible patterns."""
        edit_data = {}

        # Extract product ID (traditional method)
        id_match = re.search(r"(?:producto|id)[:\s]*(\d+)", message, re.IGNORECASE)
        if id_match:
            edit_data["product_id"] = int(id_match.group(1))

        # Extract product name for search (more flexible patterns)
        product_name = None

        # Pattern 1: "Actualizar [PRODUCT_NAME] a/precio..."
        update_match = re.search(
            r"actualizar\s+([^a-z]+?)(?:\s+a\s+|\s+precio\s+)", message, re.IGNORECASE
        )
        if update_match:
            product_name = update_match.group(1).strip()

        # Pattern 2: "Editar [PRODUCT_NAME] cambiar..." or "Editar producto [PRODUCT_NAME], ..."
        edit_patterns = [
            r"editar\s+producto\s+([^,]+?)(?:\s*,|\s+cambiar|\s+precio|\s+cantidad)",  # "Editar producto [NAME], ..."
            r"editar\s+([^,]+?)(?:\s*,|\s+cambiar|\s+precio|\s+cantidad)",  # "Editar [NAME], ..."
        ]

        for pattern in edit_patterns:
            edit_match = re.search(pattern, message, re.IGNORECASE)
            if edit_match:
                potential_name = edit_match.group(1).strip()
                # Skip if it's just "producto" or starts with "id"
                if (
                    not potential_name.lower().startswith("id")
                    and potential_name.lower() != "producto"
                ):
                    product_name = potential_name
                    break

        # Pattern 3: Traditional "nombre: [NAME]"
        name_match = re.search(
            r'nombre[:\s]*["\']([^"\']+)["\']|nombre[:\s]*([^,\n]+)',
            message,
            re.IGNORECASE,
        )
        if name_match:
            edit_data["name"] = (name_match.group(1) or name_match.group(2)).strip()

        # Store product name for search if found
        if product_name:
            edit_data["search_name"] = product_name

        # Extract new price (multiple patterns)
        price_patterns = [
            r"precio[:\s]*a[:\s]*\$?(\d+(?:\.\d{2})?)",  # "precio a $1500"
            r"precio[:\s]*\$?(\d+(?:\.\d{2})?)",  # "precio $1500"
            r"\$(\d+(?:\.\d{2})?)",  # "$1500"
        ]

        for pattern in price_patterns:
            price_match = re.search(pattern, message, re.IGNORECASE)
            if price_match:
                edit_data["price"] = float(price_match.group(1))
                break

        # Extract new quantity (multiple patterns)
        quantity_patterns = [
            r"a\s+(\d+)\s+productos?",  # "a 15 productos"
            r"cantidad[:\s,]*a[:\s]*(\d+)",  # "cantidad a 15" or "cantidad, a 15"
            r"cantidad[:\s,]*(\d+)",  # "cantidad 15" or "cantidad: 15"
            r"(\d+)\s+unidades?",  # "15 unidades"
            r",\s*cantidad\s+a\s+(\d+)",  # ", cantidad a 15"
        ]

        for pattern in quantity_patterns:
            quantity_match = re.search(pattern, message, re.IGNORECASE)
            if quantity_match:
                edit_data["quantity"] = int(quantity_match.group(1))
                break

        # Return data if we have either product_id or search_name
        return (
            edit_data
            if (edit_data.get("product_id") or edit_data.get("search_name"))
            else None
        )

    def _parse_sale_data(self, message: str) -> Dict[str, Any]:
        """Parse sale data from natural language message with multiple products support."""
        sale_data = {"items": []}

        # Extract customer information
        customer_patterns = [
            r"cliente\s+([^,\n]+?)(?:\s*,|\s*$)",  # "cliente Andres"
            r"a\s+cliente\s+([^,\n]+?)(?:\s*,|\s*$)",  # "a cliente Andres"
            r"para\s+cliente\s+([^,\n]+?)(?:\s*,|\s*$)",  # "para cliente Andres"
            r"cliente\s+id\s*(\d+)",  # "cliente ID 1"
            r"customer\s+([^,\n]+?)(?:\s*,|\s*$)",  # "customer John"
        ]

        for pattern in customer_patterns:
            customer_match = re.search(pattern, message, re.IGNORECASE)
            if customer_match:
                customer_info = customer_match.group(1).strip()
                if customer_info.isdigit():
                    sale_data["customer"] = {"type": "id", "value": int(customer_info)}
                else:
                    sale_data["customer"] = {"type": "name", "value": customer_info}
                break

        # Extract multiple products with quantities
        # Pattern 1: "Vender 3 unidades de TV, 4 de vajilla, 5 de laptop"
        products_pattern = (
            r"(\d+)\s+(?:unidades?\s+)?de\s+([^,]+?)(?:\s*,|\s+a\s+cliente|\s*$)"
        )
        product_matches = re.findall(products_pattern, message, re.IGNORECASE)

        for quantity_str, product_name in product_matches:
            sale_data["items"].append(
                {"product_name": product_name.strip(), "quantity": int(quantity_str)}
            )

        # Pattern 2: "Producto Laptop cantidad 2, Televisor x3"
        if not sale_data["items"]:
            # Try alternative patterns
            alt_patterns = [
                r"producto\s+([^,]+?)\s+cantidad\s+(\d+)",  # "producto Laptop cantidad 2"
                r"([^,]+?)\s+x(\d+)",  # "Televisor x3"
                r"([^,]+?)\s+cantidad\s+(\d+)",  # "Laptop cantidad 2"
                r"(\d+)\s+([^,]+?)(?:\s*,|\s+a\s+cliente|\s*$)",  # "2 Laptops" or "2 Laptops, 1 TV"
            ]

            for pattern in alt_patterns:
                matches = re.findall(pattern, message, re.IGNORECASE)
                for match in matches:
                    if pattern.startswith(r"producto") or pattern.endswith(
                        r"cantidad\s+(\d+)"
                    ):
                        product_name, quantity_str = match
                    else:
                        if match[0].isdigit():
                            quantity_str, product_name = match
                        else:
                            product_name, quantity_str = match

                    # Clean up product name (remove plural 's' if present)
                    product_name = product_name.strip()
                    if product_name.lower().endswith("s") and len(product_name) > 3:
                        # Try singular form for better matching
                        singular_name = product_name[:-1]
                        product_name = singular_name

                    sale_data["items"].append(
                        {
                            "product_name": product_name.strip(),
                            "quantity": int(quantity_str),
                        }
                    )

        # Extract payment method if specified
        payment_patterns = [
            r"pago\s+([^,\n]+)",  # "pago efectivo"
            r"método\s+([^,\n]+)",  # "método tarjeta"
            r"payment\s+([^,\n]+)",  # "payment cash"
        ]

        for pattern in payment_patterns:
            payment_match = re.search(pattern, message, re.IGNORECASE)
            if payment_match:
                payment_method = payment_match.group(1).strip().lower()
                if "efectivo" in payment_method or "cash" in payment_method:
                    sale_data["payment_method"] = "cash"
                elif "tarjeta" in payment_method or "credit" in payment_method:
                    sale_data["payment_method"] = "credit_card"
                else:
                    sale_data["payment_method"] = "credit_card"
                break

        return (
            sale_data
            if (sale_data.get("customer") and sale_data.get("items"))
            else None
        )

    async def _resolve_customer(self, customer_info: Dict[str, Any]) -> Optional[int]:
        """Resolve customer by ID or name, create if not exists."""
        if not customer_info:
            return None

        try:
            if customer_info["type"] == "id":
                # Search by ID
                customer_id = customer_info["value"]
                customer = await self.db_service.get_customer_by_id(customer_id)
                return customer.id if customer else None

            elif customer_info["type"] == "name":
                # Search by name or create new
                customer_name = customer_info["value"]
                all_customers = await self.db_service.get_all_customers()

                # Try to find existing customer
                for customer in all_customers:
                    if (
                        customer_name.lower() in customer.name.lower()
                        or customer.name.lower() in customer_name.lower()
                    ):
                        return customer.id

                # Create new customer if not found
                new_customer = await self.db_service.create_customer(
                    name=customer_name,
                    email=f"{customer_name.lower().replace(' ', '.')}@example.com",
                )
                return new_customer.id

        except Exception as e:
            logger.error(f"Error resolving customer: {str(e)}")
            return None

        return None

    def _get_help_response(self) -> ChatResponse:
        """Return help response with available commands."""
        help_text = """🤖 **SmartStock AI - Transformando la Gestión de Inventario**

**Comandos disponibles:**

📦 **Gestión de Inventario:**
- *"Añadir producto: Laptop, precio $500, cantidad 10"*
- *"Ver inventario"* o *"Mostrar productos"*
- *"Actualizar Vajilla de porcelana a 15 productos"*
- *"Actualizar Televisor precio a 800"*
- *"Editar producto Vajilla de porcelana, cantidad a 15"*
- *"Editar producto ID 1, cambiar precio a $600"*
- *"Análisis de inventario"*

🛒 **Gestión de Ventas:**
- *"Vender 3 unidades de TV, 4 de vajilla a cliente Andres"*
- *"Crear venta: Cliente ID 1, Producto Laptop cantidad 2"*
- *"Nueva orden: Cliente Juan, Televisor x1, Laptop x2"*

💰 **Análisis de Ventas:**
- *"Análisis de ventas"* o *"Mostrar ingresos"*
- *"Rendimiento de cliente"*

📧 **Envío de Reportes por Email:**
- *"Enviar reporte de inventario a admin@empresa.com"* (genera automáticamente)
- *"Mandar análisis de ventas a correo@ejemplo.com"* (genera automáticamente)
- *"Send inventory report to user@domain.com"* (genera automáticamente)

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
        """Handle email sending requests with automatic report generation."""
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

            # Determine report type from message content
            message_lower = message.lower()
            requested_report_type = None

            # Check for specific report type requests using word boundaries
            # Sales keywords with word boundaries to avoid partial matches
            sales_patterns = [
                r"\bventas\b",
                r"\bsales\b",
                r"\bingresos\b",
                r"\brevenue\b",
                r"\brendimiento\b",
                r"\bventa\b",
                r"\borders\b",
                r"\bórdenes\b",
                r"\bclientes\b",
                r"\bcustomers\b",
            ]

            if any(re.search(pattern, message_lower) for pattern in sales_patterns):
                requested_report_type = "sales"
            else:
                # Inventory keywords with word boundaries
                inventory_patterns = [
                    r"\binventario\b",
                    r"\binventory\b",
                    r"\bproductos\b",
                    r"\bproducts\b",
                    r"\bstock\b",
                    r"\balmacén\b",
                    r"\bwarehouse\b",
                    r"\bexistencias\b",
                ]

                if any(
                    re.search(pattern, message_lower) for pattern in inventory_patterns
                ):
                    requested_report_type = "inventory"

            # Get analysis data from cache first
            last_analysis_type, last_analysis_data = self._get_analysis_from_cache()

            # If no specific type requested, use cached analysis
            if not requested_report_type and last_analysis_type:
                requested_report_type = last_analysis_type
                logger.info(f"📧 Using cached analysis type: {requested_report_type}")
            elif not requested_report_type:
                # Default to inventory if no cache and no specific request
                requested_report_type = "inventory"
                logger.info(f"📧 Defaulting to inventory analysis")

            # Generate or use cached analysis data
            if requested_report_type == "sales":
                report_type = "Análisis de Ventas"
                charts = await self._regenerate_sales_charts()

                # Get fresh sales data for summary - calculate from order total_amount
                orders = await self.db_service.get_all_orders()
                total_sales = sum(order.total_amount or 0 for order in orders)
                summary = f"Análisis de ventas - Total: ${total_sales:,.2f}, Órdenes: {len(orders)}"

            elif requested_report_type == "inventory":
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
            # Always provide analysis data to ensure HTML embedded images (not attachments)
            if not last_analysis_data:
                # Generate basic analysis data for HTML formatting
                if requested_report_type == "sales":
                    orders = await self.db_service.get_all_orders()
                    total_sales = sum(order.total_amount or 0 for order in orders)
                    analysis_data_to_send = {
                        "total_orders": len(orders),
                        "total_sales": total_sales,
                        "average_order": total_sales / len(orders) if orders else 0,
                        "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "report_type": report_type,
                    }
                else:
                    # Basic inventory data
                    products = await self.db_service.get_all_products()
                    analysis_data_to_send = {
                        "summary": {
                            "total_items": len(products),
                            "total_units": sum(
                                getattr(p, "quantity", 0) for p in products
                            ),
                            "total_value": sum(
                                p.price * getattr(p, "quantity", 0) for p in products
                            ),
                            "critical_items_count": 0,
                        },
                        "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "report_type": report_type,
                    }
            else:
                analysis_data_to_send = last_analysis_data

            success = send_analysis_report(
                recipient_email=recipient_email,
                report_type=report_type,
                charts=charts,
                summary=summary,
                analysis_data=analysis_data_to_send,
            )

            if success:
                # Determine if analysis was generated fresh or from cache
                generation_info = ""
                if last_analysis_data:
                    generation_info = "(usando análisis previo)"
                else:
                    generation_info = "(generado automáticamente)"

                return ChatResponse(
                    response=f"✅ **Reporte enviado exitosamente** 📧\n\n"
                    f"**Destinatario:** {recipient_email}\n"
                    f"**Tipo:** {report_type} {generation_info}\n"
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

            logger.info(
                f"📊 Sales charts: Found {len(orders)} orders for chart generation"
            )

            # Generate charts metadata (same logic as in _handle_sales_analysis)
            charts_metadata = await self._generate_sales_charts(
                orders, customers, analytics_data
            )

            logger.info(
                f"📊 Sales charts: Generated {len(charts_metadata)} chart metadata objects"
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

                logger.info(
                    f"📊 Processing chart {i+1}: {chart_metadata.get('title', 'N/A')} (type: {chart_metadata.get('type', 'N/A')})"
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
                    logger.info(f"✅ Chart {i+1} generated successfully")
                else:
                    logger.warning(f"❌ Chart {i+1} failed to generate")

            logger.info(
                f"📊 Sales charts: Successfully generated {len(email_charts)} charts for email"
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

            logger.info(
                f"📊 Generating chart: {title}, type: {chart_type}, data points: {len(data)}"
            )

            if not data:
                logger.warning(f"📊 No data available for chart: {title}")
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
