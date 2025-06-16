"""
Chat Orchestrator - Main entry point for processing user messages.

This orchestrator classifies user intents and delegates to specialized agents
providing a clean, efficient multi-agent architecture.
"""

import logging
from datetime import datetime
from typing import Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession

from models.api_models import ChatResponse
from services.intent_classifier import IntentClassifier, IntentType
from services.product_agent import ProductAgent
from services.sales_agent import SalesAgent
from services.email_agent import EmailAgent
from services.inventory_agent import InventoryAgent
from services.database_service import DatabaseService


logger = logging.getLogger(__name__)

# Global cache for analysis data (simple in-memory cache)
_analysis_cache = {
    "last_analysis_type": None,
    "last_analysis_data": None,
    "timestamp": None,
}


class ChatOrchestrator:
    """
    Main orchestrator for processing chat messages and delegating to specialized agents.

    Provides efficient multi-agent architecture with better separation of concerns.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.db_service = DatabaseService(session)

        # Initialize classifier and agents
        self.intent_classifier = IntentClassifier()
        self.product_agent = ProductAgent(session)
        self.sales_agent = SalesAgent(session)
        self.email_agent = EmailAgent(session)
        self.inventory_agent = InventoryAgent(session)

        logger.info("🎼 ChatOrchestrator initialized with specialized agents")

    async def process_message(self, message: str) -> ChatResponse:
        """
        Process incoming chat message by classifying intent and delegating to appropriate agent.

        Args:
            message: User's natural language message

        Returns:
            ChatResponse with the agent's response
        """
        try:
            logger.info(f"🎼 ORCHESTRATOR: Processing message: {message[:100]}...")

            # Classify the user's intent
            intent_result = self.intent_classifier.classify_intent(message)
            intent_type = intent_result["intent"]
            confidence = intent_result["confidence"]
            parameters = intent_result["parameters"]

            logger.info(
                f"🔍 Classified intent: {intent_type.value} (confidence: {confidence:.2f})"
            )

            # Delegate to appropriate agent based on intent
            if intent_type == IntentType.ADD_PRODUCT:
                return await self.product_agent.handle_add_product(
                    parameters["message"]
                )

            elif intent_type == IntentType.EDIT_INVENTORY:
                return await self.product_agent.handle_edit_inventory(
                    parameters["message"]
                )

            elif intent_type == IntentType.LIST_INVENTORY:
                return await self._handle_list_inventory()

            elif intent_type == IntentType.INVENTORY_ANALYSIS:
                return await self._handle_inventory_analysis()

            elif intent_type == IntentType.SALES_ANALYSIS:
                return await self.sales_agent.handle_sales_analysis()

            elif intent_type == IntentType.CREATE_SALE:
                return await self.sales_agent.handle_create_sale(parameters["message"])

            elif intent_type == IntentType.EMAIL:
                return await self.email_agent.handle_email_request(
                    parameters["message"]
                )

            elif intent_type == IntentType.HELP:
                return self._get_help_response()

            else:
                logger.warning(f"🤷‍♂️ Unknown intent type: {intent_type}")
                return self._get_help_response()

        except Exception as e:
            logger.error(f"❌ Error in ChatOrchestrator.process_message: {str(e)}")
            return ChatResponse(
                response=f"❌ Error procesando mensaje: {str(e)}",
                workflow_id="orchestrator-error-"
                + datetime.now().strftime("%Y%m%d-%H%M%S"),
            )

    # === TEMPORARY HANDLERS (to be moved to specialized agents) ===

    async def _handle_list_inventory(self) -> ChatResponse:
        """Handle inventory listing - delegated to InventoryAgent in future."""
        try:
            logger.info("📋 LIST_INVENTORY: Starting inventory listing")

            analytics_data = await self.db_service.get_analytics_data()
            products_with_stock = analytics_data["inventory"]
            summary = analytics_data["summary"]

            if not products_with_stock:
                return ChatResponse(
                    response="📦 **Inventario Actual**\n\n🔍 No hay productos en el inventario. "
                    "Añade algunos productos primero usando comandos como:\n"
                    "• 'Añadir producto Laptop con precio $800 y cantidad 10'",
                    workflow_id="list-inventory-empty-"
                    + datetime.now().strftime("%Y%m%d-%H%M%S"),
                )

            # Group products by status
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

            # Build response text
            inventory_text = "📦 **Inventario Actual**\n\n"

            # Normal stock items (show first 10)
            if normal_items:
                inventory_text += "✅ **Stock Normal:**\n"
                for item in normal_items[:10]:
                    inventory_text += f"• **{item['name']}** - {item['stock_quantity']} unidades (${item['price']:.2f} c/u)\n"
                if len(normal_items) > 10:
                    inventory_text += f"... y {len(normal_items) - 10} productos más\n"
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
                    "summary": frontend_summary,
                    "normal_items": len(normal_items),
                    "low_items": len(low_items),
                    "critical_items": len(critical_items),
                    "out_of_stock": len(out_of_stock),
                    "total_value": sum(
                        p["price"] * p["stock_quantity"] for p in products_with_stock
                    ),
                },
                workflow_id="list-inventory-"
                + datetime.now().strftime("%Y%m%d-%H%M%S"),
            )

        except Exception as e:
            logger.error(f"Error in _handle_list_inventory: {str(e)}")
            return ChatResponse(
                response=f"❌ Error listando inventario: {str(e)}",
                workflow_id="list-inventory-error-"
                + datetime.now().strftime("%Y%m%d-%H%M%S"),
            )

    async def _handle_inventory_analysis(self) -> ChatResponse:
        """Handle inventory analysis - delegated to InventoryAgent."""
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

    def _get_help_response(self) -> ChatResponse:
        """Provide help information to the user."""
        help_text = """🤖 **SmartStock AI - Asistente de Inventario**

**📦 Gestión de Productos:** ✅ *ProductAgent*
• `Añadir producto [nombre] con precio $[X] y cantidad [Y]`
• `Editar producto ID [X], cambiar precio a $[Y]`
• `Ver inventario` - Listar todos los productos

**📊 Análisis:** ✅ *InventoryAgent*
• `Análisis de inventario` - Análisis completo con IA
• `Ejecutar análisis` - Análisis de stock y recomendaciones

**🛒 Ventas:** ✅ *SalesAgent*
• `Vender [cantidad] [producto] a cliente [nombre]`
• `Análisis de ventas` - Reportes de ingresos y tendencias
• `Crear venta: Cliente Juan, 2 Laptops x3, TV x1`

**📧 Reportes:** ✅ *EmailAgent*
• `Enviar reporte de inventario a [email]`
• `Mandar análisis de ventas a [email]`
• `Enviar informe de productos a admin@empresa.com`

**Ejemplo:**
_"Añadir producto Laptop con precio $800 y cantidad 10, categoría electrónicos"_
_"Vender 2 unidades de Laptop a cliente María"_
_"Enviar reporte de inventario a gerente@empresa.com"_

¿En qué puedo ayudarte hoy? 🚀"""

        return ChatResponse(
            response=help_text,
            workflow_id="help-" + datetime.now().strftime("%Y%m%d-%H%M%S"),
        )

    # === CACHE MANAGEMENT (shared functionality) ===

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
