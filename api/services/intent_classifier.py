"""
Intent Classifier for analyzing user messages and determining the appropriate agent.
"""

import re
from enum import Enum
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class IntentType(Enum):
    """Enumeration of supported intent types."""

    EMAIL = "email"
    ADD_PRODUCT = "add_product"
    CREATE_SALE = "create_sale"
    LIST_INVENTORY = "list_inventory"
    INVENTORY_ANALYSIS = "inventory_analysis"
    SALES_ANALYSIS = "sales_analysis"
    EDIT_INVENTORY = "edit_inventory"
    HELP = "help"
    UNKNOWN = "unknown"


class IntentClassifier:
    """Service for classifying user intents from natural language messages."""

    def classify_intent(self, message: str) -> Dict[str, Any]:
        """
        Classify the intent of a user message.

        Args:
            message: The user's message

        Returns:
            Dictionary containing intent type, confidence, and extracted parameters
        """
        message_lower = message.lower()
        logger.info(f"🔍 Classifying intent for: {message[:50]}...")

        # Email sending requests (highest priority)
        if self._is_email_intent(message_lower, message):
            return {
                "intent": IntentType.EMAIL,
                "confidence": 0.9,
                "parameters": {"message": message},
            }

        # Add product commands
        elif self._is_add_product_intent(message_lower):
            return {
                "intent": IntentType.ADD_PRODUCT,
                "confidence": 0.85,
                "parameters": {"message": message},
            }

        # Create sale/order commands (higher priority than general analysis)
        elif self._is_create_sale_intent(message_lower):
            return {
                "intent": IntentType.CREATE_SALE,
                "confidence": 0.85,
                "parameters": {"message": message},
            }

        # Simple inventory listing (specific patterns first)
        elif self._is_list_inventory_intent(message_lower):
            return {
                "intent": IntentType.LIST_INVENTORY,
                "confidence": 0.8,
                "parameters": {},
            }

        # Inventory analysis
        elif self._is_inventory_analysis_intent(message_lower):
            return {
                "intent": IntentType.INVENTORY_ANALYSIS,
                "confidence": 0.8,
                "parameters": {},
            }

        # Sales analysis
        elif self._is_sales_analysis_intent(message_lower):
            return {
                "intent": IntentType.SALES_ANALYSIS,
                "confidence": 0.8,
                "parameters": {},
            }

        # Edit inventory (exclude add commands)
        elif self._is_edit_inventory_intent(message_lower):
            return {
                "intent": IntentType.EDIT_INVENTORY,
                "confidence": 0.75,
                "parameters": {"message": message},
            }

        # Default help response
        else:
            return {"intent": IntentType.HELP, "confidence": 0.5, "parameters": {}}

    def _is_email_intent(self, message_lower: str, original_message: str) -> bool:
        """Check if message is about sending emails."""
        email_keywords = [
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
        has_email_keyword = any(keyword in message_lower for keyword in email_keywords)
        has_email_address = "@" in original_message or "correo" in message_lower
        return has_email_keyword and has_email_address

    def _is_add_product_intent(self, message_lower: str) -> bool:
        """Check if message is about adding products."""
        add_keywords = [
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
        has_add_keyword = any(keyword in message_lower for keyword in add_keywords)

        # Also detect patterns like "Añade el producto X con..."
        has_add_pattern = bool(
            re.search(
                r"(?:añade|añadir|agregar|agrega|crear)\s+(?:el\s+)?producto",
                message_lower,
            )
        )

        return has_add_keyword or has_add_pattern

    def _is_create_sale_intent(self, message_lower: str) -> bool:
        """Check if message is about creating sales/orders."""
        sale_keywords = [
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
        has_sale_keyword = any(keyword in message_lower for keyword in sale_keywords)

        # Also detect patterns like "2 Laptops, 1 TV a cliente"
        has_sale_pattern = bool(
            re.search(r"\d+\s+\w+.*a\s+cliente", message_lower)
            or re.search(r"vender\s+\d+", message_lower)
        )

        return has_sale_keyword or has_sale_pattern

    def _is_list_inventory_intent(self, message_lower: str) -> bool:
        """Check if message is about listing inventory."""
        list_keywords = [
            "ver inventario",
            "que elementos",
            "elementos hay",
            "qué hay en",
            "listar inventario",
            "mostrar productos",
            "list inventory",
            "show inventory",
        ]
        return any(keyword in message_lower for keyword in list_keywords)

    def _is_inventory_analysis_intent(self, message_lower: str) -> bool:
        """Check if message is about inventory analysis."""
        analysis_keywords = [
            "análisis de inventario",
            "analizar inventario",
            "ejecuta",
            "ejecutar",
            "analysis",
            "analyze",
            "restock",
            "run",
        ]
        return any(keyword in message_lower for keyword in analysis_keywords)

    def _is_sales_analysis_intent(self, message_lower: str) -> bool:
        """Check if message is about sales analysis."""
        sales_keywords = [
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
        return any(keyword in message_lower for keyword in sales_keywords)

    def _is_edit_inventory_intent(self, message_lower: str) -> bool:
        """Check if message is about editing inventory."""
        edit_keywords = [
            "editar",
            "modificar",
            "actualizar",
            "cambiar",
            "edit",
            "modify",
            "update",
            "change",
        ]
        target_keywords = ["producto", "inventario", "product", "inventory"]
        exclude_keywords = ["añadir", "añade", "agregar", "agrega", "crear", "nuevo"]

        has_edit = any(keyword in message_lower for keyword in edit_keywords)
        has_target = any(keyword in message_lower for keyword in target_keywords)
        has_exclude = any(keyword in message_lower for keyword in exclude_keywords)

        return has_edit and has_target and not has_exclude
