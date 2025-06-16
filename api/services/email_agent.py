"""
Email Agent for handling email reports and analysis export.

This agent handles all email-related functionality including report generation,
chart creation for emails, and email sending with embedded images.
"""

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from models.api_models import ChatResponse
from services.database_service import DatabaseService
from services.inventory_agent import InventoryAgent
from services.sales_agent import SalesAgent
from utils.email_utils import send_analysis_report


logger = logging.getLogger(__name__)


class EmailAgent:
    """Agent for handling email reports and analysis export."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.db_service = DatabaseService(session)
        self.inventory_agent = InventoryAgent(session)
        self.sales_agent = SalesAgent(session)
        logger.info("📧 EmailAgent initialized")

    async def handle_email_request(self, message: str) -> ChatResponse:
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
            requested_report_type = self._detect_report_type(message_lower)

            logger.info(f"📧 Detected report type: {requested_report_type}")

            # Generate report based on type
            if requested_report_type == "sales":
                return await self._handle_sales_email_report(recipient_email)
            elif requested_report_type == "inventory":
                return await self._handle_inventory_email_report(recipient_email)
            else:
                return ChatResponse(
                    response="❌ Tipo de análisis no reconocido para envío por email. "
                    "Especifica 'inventario' o 'ventas' en tu mensaje.",
                    workflow_id="email-unknown-type-"
                    + datetime.now().strftime("%Y%m%d-%H%M%S"),
                )

        except Exception as e:
            logger.error(f"Error in handle_email_request: {str(e)}")
            return ChatResponse(
                response=f"❌ Error procesando solicitud de email: {str(e)}",
                workflow_id="email-error-" + datetime.now().strftime("%Y%m%d-%H%M%S"),
            )

    def _detect_report_type(self, message_lower: str) -> Optional[str]:
        """Detect report type from message content using word boundaries."""

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
            return "sales"

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

        if any(re.search(pattern, message_lower) for pattern in inventory_patterns):
            return "inventory"

        # Default to inventory if no specific type detected
        return "inventory"

    async def _handle_inventory_email_report(
        self, recipient_email: str
    ) -> ChatResponse:
        """Handle inventory email report generation and sending."""
        try:
            logger.info(f"📧 Generating inventory report for {recipient_email}")

            # Generate fresh inventory analysis
            result = await self.inventory_agent.analyze_inventory()

            if not result["success"]:
                return ChatResponse(
                    response=f"❌ No se pudo generar el reporte de inventario: {result['error']}. "
                    "Añade algunos productos primero.",
                    workflow_id="email-inventory-error-"
                    + datetime.now().strftime("%Y%m%d-%H%M%S"),
                )

            # Get analytics data for summary
            analytics_data = await self.db_service.get_analytics_data()
            summary = analytics_data["summary"]

            # Prepare analysis data for email
            analysis_data = {
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
                "report_type": "Análisis de Inventario",
            }

            # Generate charts for email
            charts = await self._regenerate_inventory_charts()

            # Send email with complete analysis data
            success = send_analysis_report(
                recipient_email=recipient_email,
                report_type="Análisis de Inventario",
                charts=charts,
                summary=f"Análisis completo del estado actual del inventario - {summary.get('total_products', 0)} productos",
                analysis_data=analysis_data,
            )

            if success:
                return ChatResponse(
                    response=f"✅ **¡Reporte enviado exitosamente!** 📧\n\n"
                    f"📊 **Análisis de Inventario** enviado a: **{recipient_email}**\n\n"
                    f"**📈 Resumen del reporte:**\n"
                    f"• Total productos: {summary.get('total_products', 0)}\n"
                    f"• Total unidades: {summary.get('total_units', 0)}\n"
                    f"• Valor total: ${result['analysis']['total_value']:.2f}\n"
                    f"• Productos críticos: {result['analysis']['low_stock_count']}\n"
                    f"• Gráficos incluidos: {len(charts)}\n\n"
                    f"📅 **Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
                    f"El reporte incluye gráficos embebidos y análisis detallado.",
                    workflow_id=f"email-inventory-sent-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                )
            else:
                return ChatResponse(
                    response=f"❌ **Error enviando el reporte** por email a {recipient_email}. "
                    "Verifica la configuración del servidor de email.",
                    workflow_id="email-inventory-failed-"
                    + datetime.now().strftime("%Y%m%d-%H%M%S"),
                )

        except Exception as e:
            logger.error(f"Error in _handle_inventory_email_report: {str(e)}")
            return ChatResponse(
                response=f"❌ Error generando reporte de inventario: {str(e)}",
                workflow_id="email-inventory-error-"
                + datetime.now().strftime("%Y%m%d-%H%M%S"),
            )

    async def _handle_sales_email_report(self, recipient_email: str) -> ChatResponse:
        """Handle sales email report generation and sending."""
        try:
            logger.info(f"📧 Generating sales report for {recipient_email}")

            # Generate fresh sales analysis
            sales_response = await self.sales_agent.handle_sales_analysis()

            if not sales_response.data:
                return ChatResponse(
                    response="❌ No se pudo generar el reporte de ventas. "
                    "Realiza algunas ventas primero.",
                    workflow_id="email-sales-error-"
                    + datetime.now().strftime("%Y%m%d-%H%M%S"),
                )

            # Prepare analysis data for email
            analysis_data = {
                "analysis_type": "sales",
                "total_orders": sales_response.data.get("total_orders", 0),
                "total_sales": sales_response.data.get("total_sales", 0),
                "average_order": sales_response.data.get("average_order", 0),
                "total_customers": sales_response.data.get("total_customers", 0),
                "status_counts": sales_response.data.get("status_counts", {}),
                "analysis_date": sales_response.data.get("analysis_date"),
                "report_type": "Análisis de Ventas",
            }

            # Generate charts for email
            charts = await self._regenerate_sales_charts()

            # Send email with complete analysis data
            success = send_analysis_report(
                recipient_email=recipient_email,
                report_type="Análisis de Ventas",
                charts=charts,
                summary=f"Análisis de ventas - Total: ${analysis_data['total_sales']:,.2f}, Órdenes: {analysis_data['total_orders']}",
                analysis_data=analysis_data,
            )

            if success:
                return ChatResponse(
                    response=f"✅ **¡Reporte enviado exitosamente!** 📧\n\n"
                    f"💰 **Análisis de Ventas** enviado a: **{recipient_email}**\n\n"
                    f"**📈 Resumen del reporte:**\n"
                    f"• Total órdenes: {analysis_data['total_orders']}\n"
                    f"• Ingresos totales: ${analysis_data['total_sales']:.2f}\n"
                    f"• Valor promedio por orden: ${analysis_data['average_order']:.2f}\n"
                    f"• Total clientes: {analysis_data['total_customers']}\n"
                    f"• Gráficos incluidos: {len(charts)}\n\n"
                    f"📅 **Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
                    f"El reporte incluye gráficos embebidos y análisis detallado.",
                    workflow_id=f"email-sales-sent-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                )
            else:
                return ChatResponse(
                    response=f"❌ **Error enviando el reporte** por email a {recipient_email}. "
                    "Verifica la configuración del servidor de email.",
                    workflow_id="email-sales-failed-"
                    + datetime.now().strftime("%Y%m%d-%H%M%S"),
                )

        except Exception as e:
            logger.error(f"Error in _handle_sales_email_report: {str(e)}")
            return ChatResponse(
                response=f"❌ Error generando reporte de ventas: {str(e)}",
                workflow_id="email-sales-error-"
                + datetime.now().strftime("%Y%m%d-%H%M%S"),
            )

    async def _regenerate_inventory_charts(self) -> List[Dict]:
        """Regenerate inventory charts for email sending."""
        try:
            # Get fresh analysis result
            result = await self.inventory_agent.analyze_inventory()

            if not result["success"]:
                logger.warning("Could not generate inventory charts for email")
                return []

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

            logger.info(f"📊 Generated {len(email_charts)} inventory charts for email")
            return email_charts

        except Exception as e:
            logger.error(f"Error regenerating inventory charts: {str(e)}")
            return []

    async def _regenerate_sales_charts(self) -> List[Dict]:
        """Regenerate sales charts for email sending."""
        try:
            # Get fresh data
            analytics_data = await self.db_service.get_analytics_data()
            orders = analytics_data["orders"]
            customers = analytics_data["customers"]

            logger.info(
                f"📊 Sales charts: Found {len(orders)} orders for chart generation"
            )

            # Generate charts metadata using SalesAgent method
            charts_metadata = await self.sales_agent._generate_sales_charts(
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

                # Generate base64 image from metadata
                base64_image = await self._generate_chart_image(chart_metadata)

                if base64_image:
                    email_charts.append(
                        {
                            "name": chart_name,
                            "data": base64_image,
                        }
                    )

            logger.info(f"📊 Generated {len(email_charts)} sales charts for email")
            return email_charts

        except Exception as e:
            logger.error(f"Error regenerating sales charts: {str(e)}")
            return []

    async def _generate_chart_image(self, chart_metadata: Dict) -> Optional[str]:
        """Generate base64 chart image from metadata for email embedding."""
        try:
            import matplotlib

            matplotlib.use("Agg")  # Use non-interactive backend
            import matplotlib.pyplot as plt
            import base64
            from io import BytesIO

            # Set up the figure
            plt.style.use("seaborn-v0_8")
            fig, ax = plt.subplots(figsize=(10, 6))

            chart_type = chart_metadata.get("type", "bar")
            title = chart_metadata.get("title", "Chart")
            data = chart_metadata.get("data", [])

            if not data:
                plt.close(fig)
                return None

            # Generate chart based on type
            if chart_type == "bar":
                names = [item.get("name", "") for item in data]
                # Use the first numeric field found
                values = []
                for item in data:
                    for key, value in item.items():
                        if key != "name" and isinstance(value, (int, float)):
                            values.append(value)
                            break
                    else:
                        values.append(0)

                bars = ax.bar(names, values, color="#3b82f6", alpha=0.8)
                ax.set_ylabel("Valor")

                # Add value labels on bars
                for bar in bars:
                    height = bar.get_height()
                    ax.text(
                        bar.get_x() + bar.get_width() / 2.0,
                        height,
                        f"{height:.0f}",
                        ha="center",
                        va="bottom",
                    )

            elif chart_type == "line":
                names = [item.get("name", "") for item in data]
                # Use the first numeric field found
                values = []
                for item in data:
                    for key, value in item.items():
                        if key != "name" and isinstance(value, (int, float)):
                            values.append(value)
                            break
                    else:
                        values.append(0)

                ax.plot(names, values, marker="o", linewidth=2, color="#3b82f6")
                ax.set_ylabel("Valor")
                ax.grid(True, alpha=0.3)

            elif chart_type == "pie":
                names = [item.get("name", "") for item in data]
                values = [item.get("value", 0) for item in data]
                colors = ["#3b82f6", "#ef4444", "#10b981", "#f59e0b", "#8b5cf6"]

                ax.pie(
                    values,
                    labels=names,
                    autopct="%1.1f%%",
                    colors=colors[: len(values)],
                    startangle=90,
                )
                ax.axis("equal")

            # Set title and styling
            ax.set_title(title, fontsize=14, fontweight="bold", pad=20)
            plt.xticks(rotation=45, ha="right")
            plt.tight_layout()

            # Convert to base64
            buffer = BytesIO()
            plt.savefig(buffer, format="png", dpi=150, bbox_inches="tight")
            buffer.seek(0)

            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            buffer.close()
            plt.close(fig)

            return image_base64

        except Exception as e:
            logger.error(f"Error generating chart image: {str(e)}")
            if "fig" in locals():
                plt.close(fig)
            return None
