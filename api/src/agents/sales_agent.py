"""
Sales Analysis Agent for handling sales data analysis and customer insights.

This agent provides comprehensive sales analytics including performance tracking,
customer segmentation, revenue analysis, and visual dashboard generation.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from langgraph.graph import END, StateGraph

from src.agents.base_agent import AgentConfig, MultiStepAgent
from src.models import Customer, SalesOrder
from src.tools.gemini_tool import GeminiAnalysisTool
from src.tools.visualization_tool import ChartType, VisualizationTool
from src.utils import setup_logging


logger = setup_logging(__name__)


class SalesAnalysisAgent(MultiStepAgent):
    """
    Agent for comprehensive sales analysis and reporting.

    Handles sales performance tracking, customer analysis, revenue trends,
    and generates comprehensive visual dashboards for sales insights.
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        """Initialize the sales analysis agent."""
        if not config:
            config = AgentConfig(
                name="sales_analyst",
                description="Analyzes sales data and generates performance insights",
                max_iterations=10,
                tools=["gemini_analysis", "visualization", "sales_calculation"],
            )

        super().__init__(config)

        # Initialize tools
        self.gemini_tool = GeminiAnalysisTool()
        self.viz_tool = VisualizationTool()

        # Register tools
        self.register_tool("gemini_analysis", self.gemini_tool.analyze_sales_patterns)
        self.register_tool("visualization", self.viz_tool.generate_sales_trend_chart)
        self.register_tool("sales_calculation", self._calculate_sales_metrics)

        # Register step handlers
        self.register_step("initialize", self._initialize_analysis)
        self.register_step("load_sales_data", self._load_sales_data)

        self.register_step("generate_insights", self._generate_insights)
        self.register_step("create_visualizations", self._create_visualizations)
        self.register_step("create_dashboard", self._create_dashboard)
        self.register_step("finalize", self._finalize_analysis)

    def get_initial_state(self, **kwargs) -> Dict[str, Any]:
        """Get initial state for sales analysis."""
        return {
            "workflow_id": kwargs.get("workflow_id", "sales-analysis-001"),
            "status": "pending",
            "sales_orders": kwargs.get("sales_orders", []),
            "customers": kwargs.get("customers", []),
            "analysis_period_days": kwargs.get("analysis_period_days", 30),
            "include_predictions": kwargs.get("include_predictions", True),
            "generate_dashboard": kwargs.get("generate_dashboard", True),
            "analysis_types": kwargs.get(
                "analysis_types",
                [
                    "revenue_analysis",
                    "customer_segmentation",
                    "product_performance",
                    "trends",
                ],
            ),
            "comparison_period": kwargs.get("comparison_period", "previous_month"),
        }

    def build_workflow(self) -> StateGraph:
        """Build the sales analysis workflow."""
        workflow = StateGraph(dict)

        # Add nodes
        workflow.add_node("initialize", self._initialize_analysis)
        workflow.add_node("load_sales_data", self._load_sales_data)

        workflow.add_node("generate_insights", self._generate_insights)
        workflow.add_node("create_visualizations", self._create_visualizations)
        workflow.add_node("create_dashboard", self._create_dashboard)
        workflow.add_node("finalize", self._finalize_analysis)

        # Add edges
        workflow.add_edge("initialize", "load_sales_data")
        workflow.add_edge("load_sales_data", "generate_insights")
        workflow.add_edge("generate_insights", "create_visualizations")
        workflow.add_edge("create_visualizations", "create_dashboard")
        workflow.add_edge("create_dashboard", "finalize")
        workflow.add_edge("finalize", END)

        # Set entry point
        workflow.set_entry_point("initialize")

        return workflow

    def _initialize_analysis(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize the sales analysis."""
        self.logger.info("Initializing sales analysis")

        state["status"] = "running"
        state["step"] = 1
        state["current_task"] = "initialize"
        state["start_time"] = datetime.now()
        state["tools_used"] = []
        state["ai_interactions"] = 0

        return state

    def _load_sales_data(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Load and validate sales data."""
        self.logger.info("Loading sales data")

        state["step"] = 2
        state["current_task"] = "load_sales_data"

        try:
            sales_orders = state.get("sales_orders", [])
            customers = state.get("customers", [])

            # Debug logging
            self.logger.info(f"Raw sales_orders count: {len(sales_orders)}")
            self.logger.info(f"Raw customers count: {len(customers)}")
            if sales_orders:
                self.logger.info(f"First sales order sample: {sales_orders[0]}")

            # Convert to model objects if needed
            processed_orders = []
            for order in sales_orders:
                if isinstance(order, dict):
                    processed_orders.append(SalesOrder(**order))
                elif isinstance(order, SalesOrder):
                    processed_orders.append(order)

            processed_customers = []
            for customer in customers:
                if isinstance(customer, dict):
                    processed_customers.append(Customer(**customer))
                elif isinstance(customer, Customer):
                    processed_customers.append(customer)

            state["processed_orders"] = [
                order.model_dump() if hasattr(order, "model_dump") else order
                for order in processed_orders
            ]
            state["processed_customers"] = [
                customer.model_dump() if hasattr(customer, "model_dump") else customer
                for customer in processed_customers
            ]
            state["total_orders"] = len(processed_orders)
            state["total_customers"] = len(processed_customers)

            self.logger.info(
                f"Loaded {len(processed_orders)} orders and {len(processed_customers)} customers"
            )

        except Exception as e:
            self.logger.error(f"Error loading sales data: {e}")
            state["error"] = str(e)
            state["status"] = "failed"

        return state

    def _generate_insights(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI-powered insights and recommendations."""
        self.logger.info("Generating AI insights")

        state["step"] = 5
        state["current_task"] = "generate_insights"

        try:
            sales_data = state.get("processed_orders", [])
            performance_metrics = state.get("performance_metrics", {})
            customer_segments = state.get("customer_segments", {})

            # Use Gemini for AI-powered analysis
            analysis_context = {
                "sales_data": sales_data,
                "performance_metrics": performance_metrics,
                "customer_segments": customer_segments,
                "analysis_period": state.get("analysis_period_days", 30),
            }

            insights = self.gemini_tool.analyze_sales_patterns(
                sales_data=sales_data, analysis_context=analysis_context
            )

            state["ai_insights"] = insights
            state["tools_used"].append("gemini_analysis")
            state["ai_interactions"] += 1

            # Generate sales predictions if requested
            if state.get("include_predictions", True):
                self.logger.info("Generating sales predictions")
                revenue_analysis = state.get("revenue_analysis", {})

                predictions = self.gemini_tool.predict_sales_trends(
                    historical_data=sales_data, trend_analysis=revenue_analysis
                )

                state["sales_predictions"] = predictions
                self.logger.info(
                    f"Generated {len(predictions.get('predictions', []))} sales predictions"
                )

            self.logger.info("AI insights generated successfully")

        except Exception as e:
            self.logger.error(f"Error generating insights: {e}")
            state["error"] = str(e)
            state["status"] = "failed"

        return state

    def _create_visualizations(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Create individual charts and visualizations."""
        self.logger.info("Creating visualizations")

        state["step"] = 6
        state["current_task"] = "create_visualizations"

        try:
            charts = []

            # Sales trend chart
            sales_data = state.get("processed_orders", [])
            self.logger.info(f"📊 Sales data for trends: {len(sales_data)} orders")
            if sales_data:
                # Log first few orders for debugging
                self.logger.info(
                    f"🔍 Sample sales data: {sales_data[:2] if len(sales_data) >= 2 else sales_data}"
                )

                # Prepare data for trend chart
                trend_data = []
                for order in sales_data:
                    trend_data.append(
                        {
                            "date": order["order_date"],
                            "amount": float(order["total_amount"]),
                        }
                    )

                self.logger.info(f"📈 Trend data prepared: {len(trend_data)} points")
                self.logger.info(
                    f"🔍 Sample trend data: {trend_data[:2] if len(trend_data) >= 2 else trend_data}"
                )

                trend_chart = self.viz_tool.generate_sales_trend_chart(
                    trend_data, period="daily", title="Análisis de Tendencias de Ventas"
                )

                self.logger.info(f"📊 Trend chart generated: {type(trend_chart)}")
                self.logger.info(
                    f"🔍 Trend chart keys: {list(trend_chart.keys()) if isinstance(trend_chart, dict) else 'Not a dict'}"
                )

                chart_data = trend_chart.get("data", [])
                self.logger.info(f"📊 Chart data extracted: {len(chart_data)} items")
                self.logger.info(
                    f"🔍 Sample chart data: {chart_data[:2] if len(chart_data) >= 2 else chart_data}"
                )

                charts.append(
                    {
                        "type": "line",
                        "title": "Análisis de Tendencias de Ventas",
                        "chart_data": chart_data,
                    }
                )
                self.logger.info("✅ Sales trend chart added to charts list")
            else:
                self.logger.warning("⚠️ No sales data available for trend chart")

            # Product performance chart
            product_performance = state.get("product_performance", [])
            self.logger.info(
                f"📊 Product performance data: {len(product_performance)} products"
            )
            if product_performance:
                self.logger.info(
                    f"🔍 Sample product data: {product_performance[:2] if len(product_performance) >= 2 else product_performance}"
                )

                product_chart = self.viz_tool.generate_product_performance_chart(
                    product_performance,
                    metric="revenue",
                    chart_type=ChartType.BAR,
                    top_n=10,
                )

                self.logger.info(f"📊 Product chart generated: {type(product_chart)}")
                chart_data = product_chart.get("data", [])
                self.logger.info(f"📊 Product chart data: {len(chart_data)} items")

                charts.append(
                    {
                        "type": "bar",
                        "title": "Rendimiento de Mejores Productos",
                        "chart_data": chart_data,
                    }
                )
                self.logger.info("✅ Product performance chart added to charts list")
            else:
                self.logger.warning("⚠️ No product performance data available")

            # Customer segmentation chart
            customer_segments = state.get("customer_segments", {})
            self.logger.info(f"📊 Customer segments: {customer_segments}")
            if customer_segments:
                # Prepare data for customer analysis
                customer_data = []
                for customer in state.get("processed_customers", []):
                    customer_data.append(
                        {
                            "customer_id": customer["customer_id"],
                            "total_purchases": float(
                                customer.get("total_purchases", 0)
                            ),
                        }
                    )

                self.logger.info(
                    f"📊 Customer data prepared: {len(customer_data)} customers"
                )

                if customer_data:
                    customer_chart = self.viz_tool.generate_customer_analysis_chart(
                        customer_data, analysis_type="segmentation"
                    )

                    chart_data = customer_chart.get("data", [])
                    self.logger.info(f"📊 Customer chart data: {len(chart_data)} items")

                    charts.append(
                        {
                            "type": "pie",
                            "title": "Segmentación de Clientes",
                            "chart_data": chart_data,
                        }
                    )
                    self.logger.info(
                        "✅ Customer segmentation chart added to charts list"
                    )
            else:
                self.logger.warning("⚠️ No customer segments available")

            # Sales predictions chart
            sales_predictions = state.get("sales_predictions", {})
            self.logger.info(f"📊 Sales predictions: {sales_predictions}")

            if sales_predictions and sales_predictions.get("predictions"):
                predictions_data = sales_predictions.get("predictions", [])
                self.logger.info(
                    f"📊 Predictions data: {len(predictions_data)} predictions"
                )

                # Take first 10 predictions for visualization
                predictions_sample = predictions_data[:10]

                predictions_chart = self.viz_tool.generate_ai_insights_chart(
                    predictions_sample, chart_type=ChartType.LINE
                )

                chart_data = predictions_chart.get("data", [])
                self.logger.info(f"📊 Predictions chart data: {len(chart_data)} items")

                charts.append(
                    {
                        "type": "line",
                        "title": "Predicción de Ventas",
                        "chart_data": chart_data,
                    }
                )
                self.logger.info("✅ Sales predictions chart added to charts list")
            else:
                self.logger.warning("⚠️ No sales predictions available")

            state["charts"] = charts
            state["tools_used"].append("visualization")

            self.logger.info(f"🎯 TOTAL CHARTS CREATED: {len(charts)}")
            for i, chart in enumerate(charts):
                self.logger.info(
                    f"   📊 Chart {i + 1}: {chart['type']} - {len(chart.get('chart_data', []))} data points"
                )

        except Exception as e:
            self.logger.error(f"❌ Error creating visualizations: {e}")
            import traceback

            self.logger.error(f"📋 Traceback: {traceback.format_exc()}")
            # Don't fail the entire workflow for visualization errors
            state["charts"] = []
            state["chart_error"] = str(e)

        return state

    def _create_dashboard(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Create comprehensive sales dashboard."""
        self.logger.info("Creating sales dashboard")

        state["step"] = 7
        state["current_task"] = "create_dashboard"

        if not state.get("generate_dashboard", True):
            self.logger.info("Skipping dashboard generation")
            state["dashboard"] = {}
            return state

        try:
            # Prepare dashboard data
            dashboard_data = {
                "sales_data": [],
                "product_data": state.get("product_performance", []),
                "customer_segments": {},
                "payment_methods": {},
            }

            # Sales data for trend
            for order in state.get("processed_orders", []):
                dashboard_data["sales_data"].append(
                    {
                        "date": order["order_date"],
                        "amount": float(order["total_amount"]),
                    }
                )

            # Customer segments
            segments = state.get("customer_segments", {})
            if segments:
                dashboard_data["customer_segments"] = segments

            # Payment methods (mock data for demo)
            dashboard_data["payment_methods"] = {
                "Credit Card": 60,
                "Debit Card": 25,
                "Cash": 10,
                "Digital Wallet": 5,
            }

            # Generate dashboard
            dashboard = self.viz_tool.generate_dashboard(
                dashboard_data, dashboard_type="sales_overview"
            )

            state["dashboard"] = dashboard
            state["tools_used"].append("visualization")

            self.logger.info("Sales dashboard created successfully")

        except Exception as e:
            self.logger.error(f"Error creating dashboard: {e}")
            state["dashboard"] = {}
            state["dashboard_error"] = str(e)

        return state

    def _finalize_analysis(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Finalize the sales analysis."""
        self.logger.info("Finalizing sales analysis")

        state["step"] = 8
        state["current_task"] = "finalize"
        state["status"] = "completed"
        state["completion_time"] = datetime.now()

        # Create summary
        summary = {
            "total_orders_analyzed": state.get("total_orders", 0),
            "total_customers_analyzed": state.get("total_customers", 0),
            "total_revenue": state.get("performance_metrics", {}).get(
                "total_revenue", 0
            ),
            "charts_generated": len(state.get("charts", [])),
            "dashboard_created": bool(state.get("dashboard")),
            "ai_interactions": state.get("ai_interactions", 0),
            "tools_used": state.get("tools_used", []),
        }

        state["analysis_summary"] = summary

        # Create artifacts
        artifacts = []

        # Add performance metrics
        if state.get("performance_metrics"):
            artifacts.append(
                {
                    "type": "metrics",
                    "name": "performance_metrics",
                    "data": state["performance_metrics"],
                    "description": "Métricas de rendimiento de ventas",
                }
            )

        # Add AI insights
        if state.get("ai_insights"):
            artifacts.append(
                {
                    "type": "insights",
                    "name": "ai_insights",
                    "data": state["ai_insights"],
                    "description": "Insights de ventas generados por IA",
                }
            )

        # Add charts
        for chart in state.get("charts", []):
            artifacts.append(
                {
                    "type": "chart",
                    "name": f"{chart['type']}_chart",
                    "data": chart["chart_data"],
                    "description": chart["title"],
                }
            )

        # Add dashboard
        if state.get("dashboard"):
            artifacts.append(
                {
                    "type": "dashboard",
                    "name": "sales_dashboard",
                    "data": state["dashboard"],
                    "description": "Panel de ventas integral",
                }
            )

        state["artifacts"] = artifacts

        execution_time = (
            state["completion_time"] - state["start_time"]
        ).total_seconds()

        self.logger.info(
            f"Sales analysis completed in {execution_time:.2f}s. "
            f"Analyzed {summary['total_orders_analyzed']} orders, "
            f"generated {summary['charts_generated']} charts."
        )

        return state

    def _calculate_sales_metrics(
        self, sales_data: List[Dict[str, Any]], analysis_period_days: int
    ) -> Dict[str, Any]:
        """Calculate comprehensive sales metrics."""
        if not sales_data:
            return {}

        total_orders = len(sales_data)
        total_revenue = sum(float(order["total_amount"]) for order in sales_data)
        average_order_value = total_revenue / total_orders if total_orders > 0 else 0

        # Calculate period-specific metrics
        end_date = datetime.now()
        start_date = end_date - timedelta(days=analysis_period_days)

        period_orders = []
        for order in sales_data:
            order_date = order["order_date"]
            # Handle both string and datetime objects
            if isinstance(order_date, str):
                try:
                    if "T" in order_date:
                        order_datetime = datetime.fromisoformat(
                            order_date.replace("Z", "+00:00")
                        ).replace(tzinfo=None)
                    else:
                        order_datetime = datetime.fromisoformat(order_date)
                except:
                    continue
            elif isinstance(order_date, datetime):
                order_datetime = (
                    order_date.replace(tzinfo=None) if order_date.tzinfo else order_date
                )
            else:
                continue

            if start_date <= order_datetime <= end_date:
                period_orders.append(order)

        period_revenue = sum(float(order["total_amount"]) for order in period_orders)
        period_orders_count = len(period_orders)

        # Customer metrics
        unique_customers = len(set(order["customer_id"] for order in sales_data))

        return {
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "average_order_value": average_order_value,
            "period_revenue": period_revenue,
            "period_orders": period_orders_count,
            "unique_customers": unique_customers,
            "revenue_per_customer": (
                total_revenue / unique_customers if unique_customers > 0 else 0
            ),
            "orders_per_customer": (
                total_orders / unique_customers if unique_customers > 0 else 0
            ),
        }
