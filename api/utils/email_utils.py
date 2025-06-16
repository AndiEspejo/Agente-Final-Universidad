"""
Email utilities for sending reports with chart attachments.
"""

import base64
import os
import smtplib
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
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

    def send_report_email(
        self,
        recipient_email: str,
        subject: str,
        body: str,
        charts: List[Dict[str, str]],
    ) -> bool:
        """
        Send an email with multiple chart attachments.

        Args:
            recipient_email: Destination email address
            subject: Email subject
            body: Email body text
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
) -> bool:
    """
    Send an analysis report with charts via email.

    Args:
        recipient_email: Destination email
        report_type: Type of report (e.g., "Análisis de Ventas", "Análisis de Inventario")
        charts: List of chart data
        summary: Optional text summary of the analysis

    Returns:
        bool: Success status
    """
    subject = f"Reporte: {report_type}"

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
