"""
Email utilities for sending reports with chart attachments.
"""

import base64
import os
import smtplib
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email import encoders
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails with attachments."""

    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.sender_email = os.getenv("GMAIL_EMAIL")
        self.sender_password = os.getenv("GMAIL_APP_PASSWORD")

        if not self.sender_email or not self.sender_password:
            logger.warning("Gmail credentials not configured. Email sending will fail.")

    def send_analysis_report_html(
        self,
        recipient_email: str,
        subject: str,
        analysis_data: Dict,
        charts: List[Dict[str, str]],
        report_type: str = "Análisis de Inventario",
    ) -> bool:
        """
        Send a rich HTML email with embedded charts and detailed analysis.

        Args:
            recipient_email: Destination email address
            subject: Email subject
            analysis_data: Complete analysis data with insights and recommendations
            charts: List of charts with format:
                [
                    {"name": "chart1.png", "data": "base64_string"},
                    {"name": "chart2.png", "data": "base64_string"}
                ]

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart("related")
            msg["From"] = self.sender_email
            msg["To"] = recipient_email
            msg["Subject"] = subject

            # Create HTML body with embedded images
            html_body = self._create_html_report(analysis_data, charts, report_type)

            # Add HTML body
            msg.attach(MIMEText(html_body, "html"))

            # Add embedded chart images
            for i, chart in enumerate(charts):
                chart_data = chart.get("data", "")
                if not chart_data:
                    continue

                try:
                    # Remove data URL prefix if present
                    if chart_data.startswith("data:"):
                        chart_data = chart_data.split(",")[1]

                    image_data = base64.b64decode(chart_data)

                    # Create embedded image
                    img = MIMEImage(image_data)
                    img.add_header("Content-ID", f"<chart{i}>")
                    img.add_header(
                        "Content-Disposition", f"inline; filename=chart{i}.png"
                    )
                    msg.attach(img)

                except Exception as e:
                    logger.error(f"Error processing chart {i}: {e}")
                    continue

            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            text = msg.as_string()
            server.sendmail(self.sender_email, recipient_email, text)
            server.quit()

            logger.info(
                f"Rich HTML report email sent successfully to {recipient_email}"
            )
            return True

        except Exception as e:
            logger.error(f"Error sending HTML email: {e}")
            return False

    def _create_html_report(
        self,
        analysis_data: Dict,
        charts: List[Dict],
        report_type: str = "Análisis de Inventario",
    ) -> str:
        """Create rich HTML report with embedded charts and analysis."""

        # Extract analysis insights
        summary = analysis_data.get("summary", {})
        recommendations = analysis_data.get("recommendations", [])
        insights = analysis_data.get("insights", "")

        # Generate chart image tags
        chart_images = ""
        for i, chart in enumerate(charts):
            chart_name = chart.get("name", f"Chart {i+1}")
            chart_images += f"""
            <div style="margin: 20px 0; text-align: center;">
                <h3 style="color: #1f2937; margin-bottom: 10px;">{chart_name}</h3>
                <img src="cid:chart{i}" style="max-width: 100%; height: auto; border: 1px solid #e5e7eb; border-radius: 8px;" alt="{chart_name}">
            </div>
            """

        # Generate detailed analysis sections based on report type
        categories_html = ""
        if "Ventas" in report_type:
            # Sales-specific analysis sections
            if analysis_data.get("status_counts"):
                categories_html = "<h2 style='color: #1f2937; border-bottom: 2px solid #3b82f6; padding-bottom: 8px;'>📊 Estados de Órdenes</h2>"
                for status, count in analysis_data["status_counts"].items():
                    percentage = (count / analysis_data.get("total_orders", 1)) * 100
                    categories_html += f"""
                    <div style='background: #f8fafc; margin: 8px 0; padding: 15px; border-radius: 8px; border-left: 4px solid #10b981;'>
                        <h4 style='margin: 0 0 8px 0; color: #1f2937;'>{status.title()}</h4>
                        <p style='margin: 0; color: #4b5563;'>{count} órdenes ({percentage:.1f}%)</p>
                    </div>
                    """
        else:
            # Inventory analysis sections
            if analysis_data.get("categories"):
                categories_html = "<h2 style='color: #1f2937; border-bottom: 2px solid #3b82f6; padding-bottom: 8px;'>📦 Análisis por Categorías</h2>"
                sorted_categories = sorted(
                    analysis_data["categories"].items(),
                    key=lambda x: x[1].get("value", 0),
                    reverse=True,
                )
                for category, data in sorted_categories:
                    categories_html += f"""
                    <div style='background: #f8fafc; margin: 8px 0; padding: 15px; border-radius: 8px; border-left: 4px solid #10b981;'>
                        <h4 style='margin: 0 0 8px 0; color: #1f2937;'>{category}</h4>
                        <p style='margin: 0; color: #4b5563;'>{data.get('count', 0)} productos • Valor total: ${data.get('value', 0):,.2f}</p>
                    </div>
                    """

        # Generate top section HTML
        top_products_html = ""
        if "Ventas" in report_type:
            # Recent orders for sales
            if analysis_data.get("recent_orders"):
                top_products_html = "<h2 style='color: #1f2937; border-bottom: 2px solid #3b82f6; padding-bottom: 8px;'>🛒 Órdenes Recientes</h2>"
                for i, order in enumerate(analysis_data["recent_orders"][:5], 1):
                    order_date = (
                        order.get("order_date", "")[:10]
                        if order.get("order_date")
                        else "N/A"
                    )
                    top_products_html += f"""
                    <div style='background: #fef3c7; margin: 8px 0; padding: 15px; border-radius: 8px; border-left: 4px solid #f59e0b;'>
                        <h4 style='margin: 0 0 8px 0; color: #1f2937;'>{i}. Orden #{order.get('id', 'N/A')}</h4>
                        <p style='margin: 0; color: #4b5563;'>${order.get('total_amount', 0):.2f} - {order_date} - {order.get('status', 'N/A')}</p>
                    </div>
                    """
        else:
            # Top products for inventory
            if analysis_data.get("top_products"):
                top_products_html = "<h2 style='color: #1f2937; border-bottom: 2px solid #3b82f6; padding-bottom: 8px;'>💰 Productos de Mayor Valor</h2>"
                for i, product in enumerate(analysis_data["top_products"][:5], 1):
                    value = product.get("price", 0) * product.get("stock_quantity", 0)
                    top_products_html += f"""
                    <div style='background: #fef3c7; margin: 8px 0; padding: 15px; border-radius: 8px; border-left: 4px solid #f59e0b;'>
                        <h4 style='margin: 0 0 8px 0; color: #1f2937;'>{i}. {product.get('name', 'N/A')}</h4>
                        <p style='margin: 0; color: #4b5563;'>${value:,.2f} ({product.get('stock_quantity', 0)} × ${product.get('price', 0):,.2f})</p>
                    </div>
                    """

        # Generate recommendations HTML
        recommendations_html = ""
        if recommendations:
            recommendations_html = "<h2 style='color: #1f2937; border-bottom: 2px solid #3b82f6; padding-bottom: 8px;'>🎯 Recomendaciones Estratégicas</h2>"
            for rec in recommendations:
                recommendations_html += f"<div style='background: #fee2e2; margin: 8px 0; padding: 15px; border-left: 4px solid #ef4444; border-radius: 8px; color: #1f2937;'>{rec}</div>"

        # Determine report-specific content
        if "Ventas" in report_type:
            report_title = "💰 Reporte de Análisis de Ventas"
            report_emoji = "💰"
        else:
            report_title = "📊 Reporte de Análisis de Inventario"
            report_emoji = "📊"

        # Create full HTML template
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{report_title}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #374151; margin: 0; padding: 20px; background-color: #f9fafb; }}
        .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); }}
        .header {{ text-align: center; margin-bottom: 30px; padding: 20px; background: linear-gradient(135deg, #3b82f6, #1d4ed8); color: white; border-radius: 8px; }}
        .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
        .summary-card {{ background: #f8fafc; padding: 20px; border-radius: 8px; border-left: 4px solid #3b82f6; text-align: center; }}
        .summary-card h3 {{ margin: 0; font-size: 2em; color: #1f2937; }}
        .summary-card p {{ margin: 5px 0 0 0; color: #6b7280; }}
        .insights {{ background: #eff6ff; padding: 20px; border-radius: 8px; border: 1px solid #bfdbfe; margin: 20px 0; }}
        .footer {{ text-align: center; margin-top: 30px; padding: 20px; background: #f3f4f6; border-radius: 8px; color: #6b7280; }}
        h1, h2 {{ color: #1f2937; }}
        h2 {{ border-bottom: 2px solid #3b82f6; padding-bottom: 8px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{report_title}</h1>
            <p>Análisis inteligente generado automáticamente</p>
        </div>

        <h2>📈 Resumen Ejecutivo</h2>
        <div class="summary-grid">"""

        # Generate summary cards based on report type
        if "Ventas" in report_type:
            html_content += f"""
            <div class="summary-card">
                <h3>{analysis_data.get('total_orders', 0)}</h3>
                <p>Total Órdenes</p>
            </div>
            <div class="summary-card">
                <h3>${analysis_data.get('total_sales', 0):,.2f}</h3>
                <p>Ingresos Totales</p>
            </div>
            <div class="summary-card">
                <h3>${analysis_data.get('average_order', 0):,.2f}</h3>
                <p>Promedio por Orden</p>
            </div>
            <div class="summary-card">
                <h3>{analysis_data.get('total_customers', 0)}</h3>
                <p>Total Clientes</p>
            </div>"""
        else:
            # Inventory format
            html_content += f"""
            <div class="summary-card">
                <h3>{summary.get('total_items', 0)}</h3>
                <p>Total Productos</p>
            </div>
            <div class="summary-card">
                <h3>{summary.get('total_units', 0)}</h3>
                <p>Unidades en Stock</p>
            </div>
            <div class="summary-card">
                <h3>${summary.get('total_value', 0):,.2f}</h3>
                <p>Valor Total</p>
            </div>
            <div class="summary-card">
                <h3>{summary.get('critical_items_count', 0)}</h3>
                <p>Productos Críticos</p>
            </div>"""

        html_content += """
        </div>"""

        # Add insights section if available
        if insights:
            formatted_insights = (
                insights.replace("\n", "<br>")
                .replace("**", "<strong>")
                .replace("**", "</strong>")
            )
            html_content += f"""
        <div class="insights">
            <h2>🧠 Análisis Inteligente</h2>
            <div style="font-size: 14px; line-height: 1.6; color: #374151;">{formatted_insights}</div>
        </div>"""

        # Add categories and top products sections
        html_content += f"""
        {categories_html}

        {top_products_html}

        <h2>📊 Visualizaciones</h2>
        {chart_images}

        {recommendations_html}

        <div class="footer">
            <p><strong>Sistema de Ventas e Inventario</strong></p>
            <p>Reporte generado automáticamente el {analysis_data.get('analysis_date', 'N/A')}</p>
            <p>Este análisis incluye inteligencia artificial para proporcionar insights avanzados.</p>
        </div>
    </div>
</body>
</html>"""

        return html_content

    def send_report_email(
        self,
        recipient_email: str,
        subject: str,
        body: str,
        charts: List[Dict[str, str]],
    ) -> bool:
        """
        Legacy method - Send an email with multiple chart attachments (text format).
        """
        try:
            # Create message
            msg = MIMEMultipart()
            msg["From"] = self.sender_email
            msg["To"] = recipient_email
            msg["Subject"] = subject

            # Add body to email
            msg.attach(MIMEText(body, "plain"))

            # Add chart attachments
            for chart in charts:
                chart_name = chart.get("name", "chart.png")
                chart_data = chart.get("data", "")

                if not chart_data:
                    continue

                # Decode base64 image
                try:
                    # Remove data URL prefix if present (data:image/png;base64,)
                    if chart_data.startswith("data:"):
                        chart_data = chart_data.split(",")[1]

                    image_data = base64.b64decode(chart_data)

                    # Create attachment
                    attachment = MIMEBase("application", "octet-stream")
                    attachment.set_payload(image_data)
                    encoders.encode_base64(attachment)
                    attachment.add_header(
                        "Content-Disposition", f"attachment; filename= {chart_name}"
                    )
                    msg.attach(attachment)

                except Exception as e:
                    logger.error(f"Error processing chart {chart_name}: {e}")
                    continue

            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            text = msg.as_string()
            server.sendmail(self.sender_email, recipient_email, text)
            server.quit()

            logger.info(f"Report email sent successfully to {recipient_email}")
            return True

        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False


# Global email service instance
email_service = EmailService()


def send_analysis_report(
    recipient_email: str,
    report_type: str,
    charts: List[Dict[str, str]],
    summary: str = "",
    analysis_data: Dict = None,
) -> bool:
    """
    Send an analysis report with charts via email.

    Args:
        recipient_email: Destination email
        report_type: Type of report (e.g., "Análisis de Ventas", "Análisis de Inventario")
        charts: List of chart data
        summary: Optional text summary of the analysis
        analysis_data: Complete analysis data for rich HTML email

    Returns:
        bool: Success status
    """
    subject = f"📊 Reporte: {report_type}"

    # If we have complete analysis data, send rich HTML email
    if analysis_data:
        return email_service.send_analysis_report_html(
            recipient_email=recipient_email,
            subject=subject,
            analysis_data=analysis_data,
            charts=charts,
            report_type=report_type,
        )

    # Fallback to simple text email
    body = f"""
Estimado/a usuario/a,

Adjunto encontrará el reporte de {report_type.lower()} solicitado.

{summary if summary else "El reporte incluye las gráficas y análisis correspondientes."}

Este reporte fue generado automáticamente por el Sistema de Ventas e Inventario.

Saludos cordiales,
Sistema de Ventas e Inventario
    """.strip()

    return email_service.send_report_email(
        recipient_email=recipient_email, subject=subject, body=body, charts=charts
    )
