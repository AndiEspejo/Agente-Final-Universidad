"""
Chat router for natural language processing - Database Version.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from auth import User, get_current_active_user
from database import get_async_session
from models.api_models import ChatRequest, ChatResponse
from services.chat_service import ChatService


router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Process natural language chat messages for sales and inventory management.

    Supports commands like:
    - "Añadir producto: Laptop, precio $500, cantidad 10"
    - "¿Qué elementos hay en el inventario?"
    - "Ejecutar análisis de inventario"
    - "Muéstrame el análisis de ventas"
    """
    chat_service = ChatService(session)
    return await chat_service.process_message(request.message)
