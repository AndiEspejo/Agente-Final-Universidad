"""
Chat router for natural language processing - Database Version.

Powered by the multi-agent ChatOrchestrator architecture.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from auth import User, get_current_active_user
from database import get_async_session
from models.api_models import ChatRequest, ChatResponse
from services.chat_orchestrator import ChatOrchestrator


router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Process natural language chat messages for sales and inventory management.

    Powered by specialized agents for enhanced functionality:
    - ProductAgent: "Añadir producto Laptop con precio $800 y cantidad 10"
    - SalesAgent: "Vender 2 Laptops a cliente María", "Análisis de ventas"
    - InventoryAgent: "Análisis de inventario", "¿Qué elementos hay en el inventario?"
    - EmailAgent: "Enviar reporte de inventario a admin@empresa.com"
    - IntentClassifier: Intelligent intent detection with confidence scoring

    The system automatically routes requests to the appropriate specialized agent
    based on the message content and intent classification.
    """

    # Use multi-agent architecture
    orchestrator = ChatOrchestrator(session)
    return await orchestrator.process_message(request.message)
