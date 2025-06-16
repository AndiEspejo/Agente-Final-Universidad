"""
Simplified Inventory Agent for handling inventory analysis.

This agent provides focused inventory analytics including stock analysis,
categorization, and chart generation for the chat service.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from services.database_service import DatabaseService


logger = logging.getLogger(__name__)


class InventoryAgent:
    """
    Simplified agent for inventory analysis and reporting.

    Handles inventory analytics, stock status analysis, category analysis,
    and chart generation for the chat interface.
    """

    def __init__(self, session: AsyncSession):
        """Initialize the inventory agent."""
        self.session = session
        self.db_service = DatabaseService(session)
        logger.info("📦 InventoryAgent initialized")

    async def analyze_inventory(self) -> Dict[str, Any]:
        """
        Perform comprehensive inventory analysis.

        Returns:
            Dictionary containing analysis results, charts, and recommendations
        """
        try:
            logger.info("📊 Starting inventory analysis")

            # Get analytics data
            analytics_data = await self.db_service.get_analytics_data()
            products_with_stock = analytics_data["inventory"]
            summary = analytics_data["summary"]

            if not products_with_stock:
                return {
                    "success": False,
                    "error": "No hay datos suficientes para realizar el análisis",
                }

            # Perform analysis
            analysis_results = await self._perform_analysis(
                products_with_stock, summary
            )

            # Generate charts
            charts = await self._generate_charts(
                products_with_stock, analysis_results["categories"], summary
            )

            # Generate text report
            text_report = self._generate_text_report(analysis_results, summary)

            return {
                "success": True,
                "analysis": analysis_results,
                "charts": charts,
                "text_report": text_report,
                "workflow_id": f"inventory-analysis-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            }

        except Exception as e:
            logger.error(f"Error in inventory analysis: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "workflow_id": f"inventory-analysis-error-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            }

    async def _perform_analysis(
        self, products_with_stock: List[Dict], summary: Dict
    ) -> Dict[str, Any]:
        """Perform core inventory analysis calculations."""

        # Calculate total value
        total_value = sum(p["price"] * p["stock_quantity"] for p in products_with_stock)

        # Count low stock products
        low_stock_count = len(
            [
                p
                for p in products_with_stock
                if p["stock_status"] in ["crítico", "agotado"]
            ]
        )

        # Analyze categories
        categories = {}
        for product in products_with_stock:
            category = product.get("category", "Other")
            if category not in categories:
                categories[category] = {"count": 0, "value": 0}
            categories[category]["count"] += 1
            categories[category]["value"] += (
                product["price"] * product["stock_quantity"]
            )

        # Get top valuable products
        top_products = sorted(
            products_with_stock,
            key=lambda x: x["price"] * x["stock_quantity"],
            reverse=True,
        )[:3]

        # Generate recommendations
        recommendations = self._generate_recommendations(
            low_stock_count, summary["total_units"], len(categories)
        )

        return {
            "total_value": total_value,
            "low_stock_count": low_stock_count,
            "categories": categories,
            "top_products": top_products,
            "recommendations": recommendations,
            "analysis_date": datetime.now().isoformat(),
        }

    def _generate_recommendations(
        self, low_stock_count: int, total_units: int, category_count: int
    ) -> List[str]:
        """Generate actionable recommendations based on analysis."""
        recommendations = []

        if low_stock_count > 0:
            recommendations.append(
                f"🚨 **{low_stock_count} productos** necesitan reabastecimiento urgente"
            )

        if total_units < 50:
            recommendations.append(
                "📦 **Stock general bajo** - Considera aumentar inventario"
            )

        if category_count > 5:
            recommendations.append(
                f"🏷️ **{category_count} categorías** - Considera optimizar organización"
            )

        if not recommendations:
            recommendations.append(
                "✅ **Inventario saludable** - No se requieren acciones inmediatas"
            )

        return recommendations

    def _generate_text_report(self, analysis: Dict[str, Any], summary: Dict) -> str:
        """Generate formatted text report."""

        text_report = f"""📊 **Análisis Completo de Inventario**

**📈 Resumen Ejecutivo:**
- **Total productos únicos:** {summary["total_products"]}
- **Total unidades en stock:** {summary["total_units"]}
- **Valor total del inventario:** ${analysis["total_value"]:.2f}
- **Productos con stock crítico:** {analysis["low_stock_count"]}

**📦 Análisis por Categorías:**
"""

        # Sort categories by value
        sorted_categories = sorted(
            analysis["categories"].items(), key=lambda x: x[1]["value"], reverse=True
        )

        for category, data in sorted_categories[:5]:  # Top 5 categories
            text_report += (
                f"- **{category}:** {data['count']} productos (${data['value']:.2f})\n"
            )

        text_report += """
**⚠️ Alertas y Recomendaciones:**
"""

        for recommendation in analysis["recommendations"]:
            text_report += f"- {recommendation}\n"

        text_report += """
**💰 Productos de Mayor Valor:**
"""

        for i, product in enumerate(analysis["top_products"], 1):
            value = product["price"] * product["stock_quantity"]
            text_report += f"{i}. **{product['name']}** - ${value:.2f} ({product['stock_quantity']} × ${product['price']:.2f})\n"

        return text_report

    async def _generate_charts(
        self, products_with_stock: List[Dict], categories: Dict, summary: Dict
    ) -> List[Dict]:
        """Generate charts for inventory analysis."""
        try:
            charts = []

            # 1. STOCK STATUS DISTRIBUTION (Pie Chart)
            status_charts = self._create_status_distribution_chart(products_with_stock)
            if status_charts:
                charts.append(status_charts)

            # 2. CATEGORIES BY VALUE (Bar Chart)
            category_chart = self._create_category_value_chart(categories)
            if category_chart:
                charts.append(category_chart)

            # 3. TOP PRODUCTS BY VALUE (Bar Chart)
            top_products_chart = self._create_top_products_chart(products_with_stock)
            if top_products_chart:
                charts.append(top_products_chart)

            # 4. RESTOCK URGENCY (Bar Chart)
            restock_chart = self._create_restock_urgency_chart(products_with_stock)
            if restock_chart:
                charts.append(restock_chart)

            logger.info(f"📊 Generated {len(charts)} inventory charts")
            return charts

        except Exception as e:
            logger.error(f"Error generating inventory charts: {str(e)}")
            return []

    def _create_status_distribution_chart(
        self, products_with_stock: List[Dict]
    ) -> Dict:
        """Create stock status distribution pie chart."""
        status_counts = {}
        status_names = {
            "normal": "Normal",
            "bajo": "Bajo",
            "crítico": "Crítico",
            "agotado": "Agotado",
        }

        for product in products_with_stock:
            status = product["stock_status"]
            spanish_status = status_names.get(status, status.title())
            status_counts[spanish_status] = status_counts.get(spanish_status, 0) + 1

        status_data = []
        status_colors = {
            "Normal": "#22c55e",
            "Bajo": "#eab308",
            "Crítico": "#f97316",
            "Agotado": "#ef4444",
        }

        for status, count in status_counts.items():
            status_data.append(
                {
                    "name": status,
                    "value": count,
                    "color": status_colors.get(status, "#6b7280"),
                }
            )

        if status_data:
            return {
                "type": "pie",
                "title": "📊 Distribución de Estados de Stock",
                "data": status_data,
                "summary": {
                    "total_productos": len(products_with_stock),
                    "productos_criticos": len(
                        [
                            p
                            for p in products_with_stock
                            if p["stock_status"] in ["crítico", "agotado"]
                        ]
                    ),
                    "productos_saludables": len(
                        [
                            p
                            for p in products_with_stock
                            if p["stock_status"] == "normal"
                        ]
                    ),
                },
            }
        return None

    def _create_category_value_chart(self, categories: Dict) -> Dict:
        """Create category value bar chart."""
        category_data = []
        sorted_categories = sorted(
            categories.items(), key=lambda x: x[1]["value"], reverse=True
        )

        for category, data in sorted_categories[:8]:
            short_category = category if len(category) <= 15 else category[:15] + "..."
            category_data.append(
                {
                    "name": short_category,
                    "valor": round(data["value"], 2),
                }
            )

        if category_data:
            return {
                "type": "bar",
                "title": "💰 Valor de Inventario por Categoría",
                "data": category_data,
                "summary": {
                    "categoria_principal": (
                        category_data[0]["name"] if category_data else "N/A"
                    ),
                    "total_categorias": len(categories),
                    "valor_top5": round(
                        sum(item["valor"] for item in category_data[:5]), 2
                    ),
                },
            }
        return None

    def _create_top_products_chart(self, products_with_stock: List[Dict]) -> Dict:
        """Create top products by value chart."""
        top_products = sorted(
            products_with_stock,
            key=lambda x: x["price"] * x["stock_quantity"],
            reverse=True,
        )[:10]

        top_products_data = []
        for product in top_products:
            value = product["price"] * product["stock_quantity"]
            product_name = product["name"]
            short_name = (
                product_name if len(product_name) <= 12 else product_name[:12] + "..."
            )

            top_products_data.append(
                {
                    "name": short_name,
                    "valor": round(value, 2),
                    "precio": product["price"],
                }
            )

        if top_products_data:
            return {
                "type": "bar",
                "title": "🏆 Top 10 Productos por Valor Total",
                "data": top_products_data,
                "summary": {
                    "producto_principal": (
                        top_products_data[0]["name"] if top_products_data else "N/A"
                    ),
                    "valor_producto_principal": (
                        top_products_data[0]["valor"] if top_products_data else 0
                    ),
                    "valor_total_top10": round(
                        sum(p["valor"] for p in top_products_data), 2
                    ),
                },
            }
        return None

    def _create_restock_urgency_chart(self, products_with_stock: List[Dict]) -> Dict:
        """Create restock urgency chart showing only current stock."""
        urgent_restock = []
        for product in products_with_stock:
            if product["stock_status"] in ["crítico", "agotado"]:
                product_name = product["name"]
                short_name = (
                    product_name
                    if len(product_name) <= 10
                    else product_name[:10] + "..."
                )

                urgent_restock.append(
                    {
                        "name": short_name,
                        "stock_actual": product["stock_quantity"],
                        "categoria": product.get("category", "Otros"),
                        "status": product["stock_status"],
                    }
                )

        # Sort by stock quantity (ascending - lowest first) and take top 10
        urgent_restock.sort(key=lambda x: x["stock_actual"])
        urgent_restock = urgent_restock[:10]

        if urgent_restock:
            return {
                "type": "bar",
                "title": "🚨 Productos que Requieren Reabastecimiento Urgente",
                "data": urgent_restock,
                "summary": {
                    "productos_urgentes": len(urgent_restock),
                    "productos_agotados": len(
                        [p for p in urgent_restock if p["status"] == "agotado"]
                    ),
                    "productos_criticos": len(
                        [p for p in urgent_restock if p["status"] == "crítico"]
                    ),
                },
            }
        return None
