"""
Sales Agent for handling sales operations, analysis, and order management.

This agent provides comprehensive sales analysis and order creation capabilities
with natural language processing and chart generation.
"""

import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from models.api_models import ChatResponse
from services.database_service import DatabaseService


logger = logging.getLogger(__name__)


class SalesAgent:
    """Agent for handling all sales-related operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.db_service = DatabaseService(session)
        logger.info("💰 SalesAgent initialized")

    async def handle_sales_analysis(self) -> ChatResponse:
        """Handle sales analysis command with comprehensive reporting."""
        try:
            logger.info("💰 SALES_ANALYSIS: Starting comprehensive analysis")

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

            # Save to cache for email functionality
            analysis_data = {
                "total_sales": total_sales,
                "total_orders": total_orders,
                "average_order": average_order,
                "status_counts": status_counts,
                "recent_orders": recent_orders,
                "total_customers": len(customers),
                "analysis_date": datetime.now().isoformat(),
            }

            return ChatResponse(
                response=sales_text,
                charts=charts,
                data=analysis_data,
                workflow_id="sales-analysis-"
                + datetime.now().strftime("%Y%m%d-%H%M%S"),
            )

        except Exception as e:
            logger.error(f"Error in handle_sales_analysis: {str(e)}")
            return ChatResponse(
                response=f"❌ Error en análisis de ventas: {str(e)}",
                workflow_id="sales-analysis-error-"
                + datetime.now().strftime("%Y%m%d-%H%M%S"),
            )

    async def handle_create_sale(self, message: str) -> ChatResponse:
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

            for item in sale_data["items"]:
                product_name = item["product_name"]
                quantity = item["quantity"]

                # Find product by name (fuzzy matching)
                all_products = await self.db_service.get_all_products()
                product = None

                for p in all_products:
                    if (
                        product_name.lower() in p.name.lower()
                        or p.name.lower() in product_name.lower()
                    ):
                        product = p
                        break

                if not product:
                    stock_errors.append(
                        f"❌ **{product_name}**: Producto no encontrado en el inventario"
                    )
                    continue

                # Check stock availability
                current_stock = (
                    product.inventory_items[0].quantity
                    if product.inventory_items
                    else 0
                )

                if current_stock < quantity:
                    stock_errors.append(
                        f"❌ **{product.name}**: Stock insuficiente (disponible: {current_stock}, solicitado: {quantity})"
                    )
                    continue

                # Add to resolved items
                resolved_items.append(
                    {
                        "product_id": product.id,
                        "quantity": quantity,
                        "price": product.price,
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
                payment_method=sale_data.get("payment_method", "tarjeta_debito"),
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
            logger.error(f"Error in handle_create_sale: {str(e)}")
            return ChatResponse(
                response=f"❌ Error creando venta: {str(e)}",
                workflow_id="create-sale-error-"
                + datetime.now().strftime("%Y%m%d-%H%M%S"),
            )

    async def _generate_sales_charts(self, orders, customers, analytics_data):
        """Generate charts for sales analysis."""
        try:
            charts = []

            # 1. SALES TRENDS CHART (Line Chart)
            daily_sales = {}
            for order in orders:
                order_date = (
                    order.get("order_date", "")[:10] if order.get("order_date") else ""
                )
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
                        "name": date,
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
                    },
                }
            )

            # 2. TOP PRODUCTS BY REVENUE (Bar Chart)
            product_revenue = {}

            for order in orders:
                order_items = order.get("items", [])
                for item in order_items:
                    product_name = item.get(
                        "product_name", f"Producto #{item.get('product_id', 'N/A')}"
                    )
                    total_price = item.get("total_price", 0)

                    if product_name not in product_revenue:
                        product_revenue[product_name] = 0
                    product_revenue[product_name] += float(total_price)

            # Sort and get top 10 products
            sorted_products = sorted(
                product_revenue.items(), key=lambda x: x[1], reverse=True
            )[:10]

            product_data = []
            for product_name, revenue in sorted_products:
                short_name = (
                    product_name
                    if len(product_name) <= 15
                    else product_name[:15] + "..."
                )
                product_data.append(
                    {
                        "name": short_name,
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
                        },
                    }
                )

            logger.info(f"📊 Generated {len(charts)} sales charts")
            return charts

        except Exception as e:
            logger.error(f"Error generating sales charts: {str(e)}")
            return []

    def _parse_sale_data(self, message: str) -> Optional[Dict[str, Any]]:
        """Parse sale data from natural language message with multiple products support."""
        sale_data = {"items": []}

        # Extract customer information
        customer_patterns = [
            r"cliente\s+([^,\n]+?)(?:\s*,|\s*$)",
            r"a\s+cliente\s+([^,\n]+?)(?:\s*,|\s*$)",
            r"para\s+cliente\s+([^,\n]+?)(?:\s*,|\s*$)",
            r"cliente\s+id\s*(\d+)",
            r"customer\s+([^,\n]+?)(?:\s*,|\s*$)",
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
        products_pattern = (
            r"(\d+)\s+(?:unidades?\s+)?de\s+([^,]+?)(?:\s*,|\s+a\s+cliente|\s*$)"
        )
        product_matches = re.findall(products_pattern, message, re.IGNORECASE)

        for quantity_str, product_name in product_matches:
            sale_data["items"].append(
                {"product_name": product_name.strip(), "quantity": int(quantity_str)}
            )

        # Alternative patterns if first one doesn't work
        if not sale_data["items"]:
            alt_patterns = [
                r"producto\s+([^,]+?)\s+cantidad\s+(\d+)",
                r"([^,]+?)\s+x(\d+)",
                r"(\d+)\s+([^,]+?)(?:\s*,|\s+a\s+cliente|\s*$)",
            ]

            for pattern in alt_patterns:
                matches = re.findall(pattern, message, re.IGNORECASE)
                for match in matches:
                    if pattern.startswith(r"producto"):
                        product_name, quantity_str = match
                    elif "x" in pattern:
                        product_name, quantity_str = match
                    else:
                        quantity_str, product_name = match

                    product_name = product_name.strip()
                    if product_name.lower().endswith("s") and len(product_name) > 3:
                        product_name = product_name[:-1]

                    sale_data["items"].append(
                        {
                            "product_name": product_name.strip(),
                            "quantity": int(quantity_str),
                        }
                    )

        # Extract payment method if specified
        payment_patterns = [
            r"pago\s+([^,\n]+)",
            r"método\s+([^,\n]+)",
            r"payment\s+([^,\n]+)",
        ]

        for pattern in payment_patterns:
            payment_match = re.search(pattern, message, re.IGNORECASE)
            if payment_match:
                payment_method = payment_match.group(1).strip().lower()
                if "efectivo" in payment_method or "cash" in payment_method:
                    sale_data["payment_method"] = "cash"
                elif "tarjeta" in payment_method or "credit" in payment_method:
                    sale_data["payment_method"] = "tarjeta_debito"
                break
        else:
            sale_data["payment_method"] = "tarjeta_debito"

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
                customer_id = customer_info["value"]
                customer = await self.db_service.get_customer_by_id(customer_id)
                return customer.id if customer else None

            elif customer_info["type"] == "name":
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
