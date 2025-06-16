"""
Visualization tool for generating charts and graphs for sales/inventory data.

This module provides comprehensive chart generation capabilities including
sales analytics, inventory monitoring, and AI-generated insights visualization.
"""

import base64
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import matplotlib.pyplot as plt
import pandas as pd
import plotly.graph_objects as go
import seaborn as sns
from plotly.subplots import make_subplots


class ChartType:
    """Chart type constants."""

    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    SCATTER = "scatter"
    HISTOGRAM = "histogram"
    HEATMAP = "heatmap"
    FUNNEL = "funnel"
    GAUGE = "gauge"
    CANDLESTICK = "candlestick"
    DASHBOARD = "dashboard"


class VisualizationTool:
    """
    Tool for creating business intelligence visualizations.

    Provides methods to generate various charts for sales and inventory analysis
    with support for both static (matplotlib) and interactive (plotly) charts.
    """

    def __init__(self, style: str = "plotly", theme: str = "plotly_white"):
        """
        Initialize the visualization tool.

        Args:
            style: Chart library to use ('plotly' or 'matplotlib')
            theme: Visual theme for charts
        """
        self.style = style
        self.theme = theme

        # Configure matplotlib style
        if style == "matplotlib":
            plt.style.use(
                "seaborn-v0_8" if hasattr(plt.style, "seaborn-v0_8") else "default"
            )
            sns.set_palette("husl")

        # Color palettes
        self.colors = {
            "primary": "#1f77b4",
            "secondary": "#ff7f0e",
            "success": "#2ca02c",
            "danger": "#d62728",
            "warning": "#ff7f0e",
            "info": "#17a2b8",
            "light": "#f8f9fa",
            "dark": "#343a40",
        }

    def generate_sales_trend_chart(
        self,
        sales_data: List[Dict[str, Any]],
        period: str = "monthly",
        title: str = "Sales Trend Analysis",
    ) -> Dict[str, Any]:
        """
        Generate sales trend line chart.

        Args:
            sales_data: List of sales records with date and amount
            period: Aggregation period ('daily', 'weekly', 'monthly', 'yearly')
            title: Chart title

        Returns:
            Chart configuration and data
        """
        logger = logging.getLogger(__name__)

        logger.info(
            f"🔧 generate_sales_trend_chart called with {len(sales_data)} records"
        )
        logger.info(f"🔧 Period: {period}, Title: {title}")

        try:
            # Convert to DataFrame
            df = pd.DataFrame(sales_data)
            logger.info(f"🔧 DataFrame created with shape: {df.shape}")
            logger.info(f"🔧 DataFrame columns: {list(df.columns)}")

            if len(df) == 0:
                logger.warning("🔧 Empty DataFrame - returning empty data")
                return {
                    "type": ChartType.LINE,
                    "data": [],
                    "summary": {"error": "No sales data provided"},
                }

            df["date"] = pd.to_datetime(df["date"])
            df["amount"] = pd.to_numeric(df["amount"])
            logger.info(
                f"🔧 Data types converted - date sample: {df['date'].iloc[0]}, amount sample: {df['amount'].iloc[0]}"
            )

            # Aggregate by period
            if period == "daily":
                df_agg = df.groupby(df["date"].dt.date)["amount"].sum().reset_index()
                df_agg["date"] = df_agg["date"].astype(str)
            elif period == "weekly":
                df_agg = (
                    df.groupby(df["date"].dt.to_period("W"))["amount"]
                    .sum()
                    .reset_index()
                )
                df_agg["date"] = df_agg["date"].astype(str)
            elif period == "monthly":
                df_agg = (
                    df.groupby(df["date"].dt.to_period("M"))["amount"]
                    .sum()
                    .reset_index()
                )
                df_agg["date"] = df_agg["date"].astype(str)
            elif period == "yearly":
                df_agg = (
                    df.groupby(df["date"].dt.to_period("Y"))["amount"]
                    .sum()
                    .reset_index()
                )
                df_agg["date"] = df_agg["date"].astype(str)

            logger.info(f"🔧 Aggregated data shape: {df_agg.shape}")
            logger.info(
                f"🔧 Sample aggregated data: {df_agg.head(2).to_dict('records') if len(df_agg) > 0 else 'Empty'}"
            )

            # Format data for recharts (frontend expects 'name' and value columns)
            chart_data = []
            for _, row in df_agg.iterrows():
                chart_data.append(
                    {
                        "fecha": str(row["date"]),
                        "ventas": float(row["amount"]),  # Spanish label
                    }
                )

            logger.info(f"🔧 Final chart data: {len(chart_data)} points")
            logger.info(
                f"🔧 Sample final data: {chart_data[:2] if len(chart_data) >= 2 else chart_data}"
            )

            result = {
                "type": ChartType.LINE,
                "data": chart_data,
                "summary": {
                    "total_sales": float(df_agg["amount"].sum()),
                    "avg_sales": float(df_agg["amount"].mean()),
                    "trend": (
                        "aumentando"
                        if len(df_agg) > 1
                        and df_agg["amount"].iloc[-1] > df_agg["amount"].iloc[0]
                        else "estable"
                    ),
                },
            }

            logger.info(f"🔧 Returning result with {len(result['data'])} data points")
            return result

        except Exception as e:
            logger.error(f"🔧 Error in generate_sales_trend_chart: {e}")
            import traceback

            logger.error(f"🔧 Traceback: {traceback.format_exc()}")
            # Return empty data structure if there's an error
            return {"type": ChartType.LINE, "data": [], "summary": {"error": str(e)}}

    def generate_product_performance_chart(
        self,
        product_data: List[Dict[str, Any]],
        metric: str = "revenue",
        chart_type: str = ChartType.BAR,
        top_n: int = 10,
    ) -> Dict[str, Any]:
        """
        Generate product performance chart.

        Args:
            product_data: List of product performance data
            metric: Metric to analyze ('revenue', 'quantity', 'profit')
            chart_type: Type of chart to generate
            top_n: Number of top products to show

        Returns:
            Chart configuration and data
        """
        try:
            df = pd.DataFrame(product_data)
            if len(df) == 0:
                return {
                    "type": chart_type,
                    "data": [],
                    "summary": {"error": "No product data available"},
                }

            df = df.nlargest(min(top_n, len(df)), metric)

            # Format data for recharts
            chart_data = []
            for _, row in df.iterrows():
                if chart_type == ChartType.PIE:
                    chart_data.append(
                        {"producto": row["product_name"], "valor": float(row[metric])}
                    )
                else:  # BAR chart
                    chart_data.append(
                        {
                            "producto": row["product_name"],
                            "ingresos": float(row.get("revenue", 0)),  # Spanish label
                            "cantidad": int(row.get("quantity", 0)),  # Spanish label
                        }
                    )

            return {
                "type": chart_type,
                "data": chart_data,
                "summary": {
                    "top_product": df.iloc[0]["product_name"] if len(df) > 0 else "N/A",
                    "top_value": float(df.iloc[0][metric]) if len(df) > 0 else 0,
                    "total_products": len(df),
                },
            }
        except Exception as e:
            return {"type": chart_type, "data": [], "summary": {"error": str(e)}}

    def generate_inventory_status_chart(
        self, inventory_data: List[Dict[str, Any]], chart_type: str = ChartType.BAR
    ) -> Dict[str, Any]:
        """
        Generate inventory status visualization.

        Args:
            inventory_data: List of inventory items with status info
            chart_type: Type of chart to generate

        Returns:
            Chart configuration and data
        """
        try:
            df = pd.DataFrame(inventory_data)
            if len(df) == 0:
                return {
                    "type": chart_type,
                    "data": [],
                    "summary": {"error": "No inventory data available"},
                }

            if chart_type == ChartType.PIE:
                # Calculate status distribution for PIE chart
                if "status" in df.columns:
                    status_counts = df["status"].value_counts()
                    chart_data = []
                    for status, count in status_counts.items():
                        chart_data.append(
                            {
                                "name": str(status).replace("_", " ").title(),
                                "value": int(count),
                            }
                        )
                else:
                    chart_data = []

            elif chart_type == ChartType.BAR:
                # Stock levels by product for BAR chart
                chart_data = []
                for _, row in df.iterrows():
                    product_name = row.get(
                        "product_name", row.get("product_sku", "Unknown")
                    )
                    chart_data.append(
                        {
                            "name": str(product_name)[:20],  # Truncate long names
                            "cantidad": int(row.get("quantity", 0)),
                            "quantity": int(row.get("quantity", 0)),
                            "minimo": int(row.get("min_threshold", 0)),
                            "min_threshold": int(row.get("min_threshold", 0)),
                        }
                    )

            # Calculate summary metrics
            low_stock_items = 0
            if "quantity" in df.columns and "min_threshold" in df.columns:
                low_stock = df[df["quantity"] <= df["min_threshold"]]
                low_stock_items = len(low_stock)

            return {
                "type": chart_type,
                "data": chart_data,
                "summary": {
                    "total_items": len(df),
                    "low_stock_items": low_stock_items,
                    "total_quantity": (
                        int(df["quantity"].sum()) if "quantity" in df.columns else 0
                    ),
                    "avg_stock_level": (
                        float(df["quantity"].mean()) if "quantity" in df.columns else 0
                    ),
                },
            }
        except Exception as e:
            return {"type": chart_type, "data": [], "summary": {"error": str(e)}}

    def generate_customer_analysis_chart(
        self, customer_data: List[Dict[str, Any]], analysis_type: str = "segmentation"
    ) -> Dict[str, Any]:
        """
        Generate customer analysis charts.

        Args:
            customer_data: List of customer data
            analysis_type: Type of analysis ('segmentation', 'lifetime_value', 'purchase_frequency')

        Returns:
            Chart configuration and data
        """
        try:
            df = pd.DataFrame(customer_data)
            if len(df) == 0:
                return {
                    "type": ChartType.PIE,
                    "data": [],
                    "summary": {"error": "No customer data available"},
                }

            if analysis_type == "segmentation":
                # Customer segmentation by purchase amount
                df["segment"] = pd.cut(
                    df["total_purchases"],
                    bins=[0, 1000, 5000, 10000, float("inf")],
                    labels=["Bronce", "Plata", "Oro", "Platino"],
                )
                segment_counts = df["segment"].value_counts()

                # Format data for recharts PIE chart
                chart_data = []
                for segment, count in segment_counts.items():
                    chart_data.append(
                        {"segmento": str(segment), "clientes": int(count)}
                    )

                return {
                    "type": ChartType.PIE,
                    "data": chart_data,
                    "summary": {
                        "total_customers": len(df),
                        "segments": segment_counts.to_dict(),
                    },
                }

            elif analysis_type == "lifetime_value":
                # Customer lifetime value distribution - use BAR chart for simplicity
                # Create value ranges
                bins = [0, 1000, 2000, 5000, 10000, float("inf")]
                labels = ["0-1K", "1K-2K", "2K-5K", "5K-10K", "10K+"]
                df["value_range"] = pd.cut(
                    df["total_purchases"], bins=bins, labels=labels
                )
                value_counts = df["value_range"].value_counts()

                chart_data = []
                for range_name, count in value_counts.items():
                    chart_data.append(
                        {"rango": str(range_name), "clientes": int(count)}
                    )

                return {
                    "type": ChartType.BAR,
                    "data": chart_data,
                    "summary": {
                        "avg_lifetime_value": float(df["total_purchases"].mean()),
                        "max_lifetime_value": float(df["total_purchases"].max()),
                        "total_customers": len(df),
                    },
                }
        except Exception as e:
            return {"type": ChartType.PIE, "data": [], "summary": {"error": str(e)}}

    def generate_ai_insights_chart(
        self, predictions: List[Dict[str, Any]], chart_type: str = ChartType.LINE
    ) -> Dict[str, Any]:
        """
        Generate charts for AI predictions and insights.

        Args:
            predictions: List of AI predictions with confidence scores
            chart_type: Type of chart to generate

        Returns:
            Chart configuration and data
        """
        try:
            df = pd.DataFrame(predictions)
            if len(df) == 0:
                return {
                    "type": ChartType.LINE,
                    "data": [],
                    "summary": {"error": "No prediction data available"},
                }

            # Format data for recharts LINE chart
            chart_data = []
            for _, row in df.iterrows():
                chart_data.append(
                    {
                        "periodo": str(row.get("period", "N/A")),
                        "prediccion": float(row.get("predicted_value", 0)),
                        "confianza": float(row.get("confidence", 0))
                        * 100,  # Convert to percentage
                    }
                )

            return {
                "type": ChartType.LINE,
                "data": chart_data,
                "summary": {
                    "avg_prediction": (
                        float(df["predicted_value"].mean())
                        if "predicted_value" in df.columns
                        else 0
                    ),
                    "confidence_avg": (
                        float(df["confidence"].mean()) * 100
                        if "confidence" in df.columns
                        else 0
                    ),
                    "trend": (
                        "aumentando"
                        if len(df) > 1
                        and df["predicted_value"].iloc[-1]
                        > df["predicted_value"].iloc[0]
                        else "estable"
                    ),
                },
            }
        except Exception as e:
            return {"type": ChartType.LINE, "data": [], "summary": {"error": str(e)}}

    def generate_dashboard(
        self, data: Dict[str, Any], dashboard_type: str = "sales_overview"
    ) -> Dict[str, Any]:
        """
        Generate comprehensive dashboard with multiple charts.

        Args:
            data: Dictionary containing various data for dashboard
            dashboard_type: Type of dashboard ('sales_overview', 'inventory_overview')

        Returns:
            Dashboard configuration with multiple charts
        """
        if dashboard_type == "sales_overview":
            # Create multi-chart dashboard
            if self.style == "plotly":
                fig = make_subplots(
                    rows=2,
                    cols=2,
                    subplot_titles=(
                        "Tendencia de Ventas",
                        "Mejores Productos",
                        "Segmentos de Clientes",
                        "Métodos de Pago",
                    ),
                    specs=[
                        [{"type": "scatter"}, {"type": "bar"}],
                        [{"type": "pie"}, {"type": "pie"}],
                    ],
                )

                # Sales trend (top left)
                sales_df = pd.DataFrame(data.get("sales_data", []))
                if not sales_df.empty:
                    fig.add_trace(
                        go.Scatter(
                            x=sales_df["date"],
                            y=sales_df["amount"],
                            mode="lines+markers",
                        ),
                        row=1,
                        col=1,
                    )

                # Top products (top right)
                products_df = pd.DataFrame(data.get("product_data", []))
                if not products_df.empty:
                    fig.add_trace(
                        go.Bar(x=products_df["product_name"], y=products_df["revenue"]),
                        row=1,
                        col=2,
                    )

                # Customer segments (bottom left)
                segments_data = data.get("customer_segments", {})
                if segments_data:
                    fig.add_trace(
                        go.Pie(
                            labels=list(segments_data.keys()),
                            values=list(segments_data.values()),
                        ),
                        row=2,
                        col=1,
                    )

                # Payment methods (bottom right)
                payment_data = data.get("payment_methods", {})
                if payment_data:
                    fig.add_trace(
                        go.Pie(
                            labels=list(payment_data.keys()),
                            values=list(payment_data.values()),
                        ),
                        row=2,
                        col=2,
                    )

                fig.update_layout(
                    height=800,
                    showlegend=False,
                    title_text="Panel de Ventas General",
                    template=self.theme,
                )

                return {
                    "type": ChartType.DASHBOARD,
                    "figure": fig.to_json(),
                    "data": data,
                    "summary": {
                        "dashboard_type": dashboard_type,
                        "charts_included": 4,
                        "data_points": sum(
                            (
                                len(v)
                                if isinstance(v, list)
                                else len(v) if isinstance(v, dict) else 0
                            )
                            for v in data.values()
                        ),
                    },
                }

    def export_chart(
        self,
        chart_data: Dict[str, Any],
        format: str = "png",
        filename: Optional[str] = None,
    ) -> str:
        """
        Export chart to file.

        Args:
            chart_data: Chart data from generate methods
            format: Export format ('png', 'pdf', 'html')
            filename: Optional filename

        Returns:
            Filename of exported chart
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"chart_{timestamp}.{format}"

        if self.style == "plotly" and "figure" in chart_data:
            fig = go.Figure(json.loads(chart_data["figure"]))

            if format == "png" or format == "pdf":
                fig.write_image(filename, width=1200, height=800, scale=2)
            elif format == "html":
                fig.write_html(filename)

        elif "image" in chart_data:
            # For matplotlib base64 images
            if format == "png":
                image_data = base64.b64decode(chart_data["image"])
                with open(filename, "wb") as f:
                    f.write(image_data)

        return filename


# Convenience functions for quick chart generation
def create_sales_trend_chart(sales_data: List[Dict], **kwargs) -> Dict[str, Any]:
    """Quick function to create sales trend chart."""
    viz = VisualizationTool()
    return viz.generate_sales_trend_chart(sales_data, **kwargs)


def create_inventory_chart(inventory_data: List[Dict], **kwargs) -> Dict[str, Any]:
    """Quick function to create inventory status chart."""
    viz = VisualizationTool()
    return viz.generate_inventory_status_chart(inventory_data, **kwargs)


def create_product_performance_chart(
    product_data: List[Dict], **kwargs
) -> Dict[str, Any]:
    """Quick function to create product performance chart."""
    viz = VisualizationTool()
    return viz.generate_product_performance_chart(product_data, **kwargs)
