"""
Analytics router for business intelligence and reporting.
"""

from fastapi import APIRouter, logger

from models.api_models import AnalysisRequest, EmailReportRequest
from utils.email_utils import send_analysis_report


router = APIRouter(tags=["analytics"])


@router.post("/analyze")
async def analyze_endpoint(request: AnalysisRequest):
    """Run comprehensive business analysis."""
    if request.analysis_type == "inventory":
        return await handle_inventory_analysis(request)
    elif request.analysis_type == "sales":
        return await handle_sales_analysis(request)

    else:
        return {"error": "Unknown analysis type"}


async def handle_inventory_analysis(request: AnalysisRequest):
    """Handle inventory analysis requests."""
    return {
        "analysis_type": "inventory",
        "data_size": request.data_size,
        "status": "completed",
        "message": "Análisis de inventario - usar endpoint /chat para análisis completo",
    }


async def handle_sales_analysis(request: AnalysisRequest):
    """Handle sales analysis requests."""
    return {
        "analysis_type": "sales",
        "data_size": request.data_size,
        "status": "completed",
        "message": "Análisis de ventas - usar endpoint /chat para análisis completo",
    }


@router.get("/workflows")
async def list_workflows():
    """List available analysis workflows."""
    return {
        "available_workflows": [
            {
                "id": "inventory_analysis",
                "name": "Análisis de Inventario",
                "description": "Análisis completo del estado del inventario con recomendaciones",
                "parameters": ["low_stock_threshold", "include_predictions"],
            },
            {
                "id": "sales_analysis",
                "name": "Análisis de Ventas",
                "description": "Análisis de rendimiento de ventas y tendencias",
                "parameters": ["analysis_period_days", "include_forecasting"],
            },
        ]
    }


@router.get("/status")
async def get_analytics_status():
    """Get analytics system status."""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "available_analyses": ["inventory", "sales"],
        "message": "Sistema de análisis funcionando correctamente",
    }


@router.post("/send-report-email/")
async def send_report_email(request: EmailReportRequest):
    """
    Send analysis report with charts via email.
    """
    try:
        success = send_analysis_report(
            recipient_email=request.recipient_email,
            report_type=request.report_type,
            charts=request.charts,
            summary=request.summary,
        )

        if success:
            return {
                "success": True,
                "message": f"Reporte enviado exitosamente a {request.recipient_email}",
            }
        else:
            return {
                "success": False,
                "message": "Error al enviar el reporte. Verifique la configuración de email.",
            }

    except Exception as e:
        logger.error(f"Error sending report email: {e}")
        return {"success": False, "message": f"Error interno: {str(e)}"}
