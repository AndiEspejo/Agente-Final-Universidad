"""
API Models for the LangGraph Sales/Inventory System.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., description="User message")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Chat context")


class ChatResponse(BaseModel):
    response: str = Field(..., description="Bot response")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Analysis data")
    charts: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Generated charts"
    )
    order: Optional[Dict[str, Any]] = Field(
        default=None, description="Order information"
    )
    workflow_id: Optional[str] = Field(
        default=None, description="Workflow execution ID"
    )


class AnalysisRequest(BaseModel):
    analysis_type: str = Field(..., description="Type of analysis")
    data_size: Optional[str] = Field(
        default="medium", description="Size of sample data"
    )
    include_charts: Optional[bool] = Field(
        default=True, description="Include chart generation"
    )


class SalesOrderRequest(BaseModel):
    customer_id: int = Field(..., description="Customer ID")
    items: List[Dict[str, Any]] = Field(..., description="Order items")
    payment_method: str = Field(default="credit_card", description="Payment method")


class ProductCreateRequest(BaseModel):
    name: str = Field(..., description="Product name")
    price: float = Field(..., description="Product price")
    quantity: int = Field(..., description="Initial stock quantity")
    category: Optional[str] = Field(default="Other", description="Product category")
    description: Optional[str] = Field(default="", description="Product description")
    sku: Optional[str] = Field(default=None, description="Product SKU")
    unit_cost: Optional[float] = Field(default=None, description="Product unit cost")
    minimum_stock: Optional[int] = Field(
        default=None, description="Minimum stock threshold"
    )
    maximum_stock: Optional[int] = Field(
        default=None, description="Maximum stock threshold"
    )


class ProductEditRequest(BaseModel):
    product_id: int = Field(..., description="Product ID to edit")
    name: Optional[str] = Field(default=None, description="New product name")
    price: Optional[float] = Field(default=None, description="New product price")
    quantity: Optional[int] = Field(default=None, description="New stock quantity")
    category: Optional[str] = Field(default=None, description="New product category")
    description: Optional[str] = Field(
        default=None, description="New product description"
    )
    minimum_stock: Optional[int] = Field(default=None, description="Stock mínimo")
    maximum_stock: Optional[int] = Field(default=None, description="Stock máximo")


class StockUpdateRequest(BaseModel):
    product_id: int = Field(..., description="Product ID to update")
    quantity: int = Field(..., description="New quantity")
    location: str = Field(
        default="Almacén Principal", description="Ubicación de inventario"
    )


class EmailReportRequest(BaseModel):
    recipient_email: str = Field(..., description="Email address to send the report")
    report_type: str = Field(
        ..., description="Type of report (e.g., 'Análisis de Ventas')"
    )
    charts: List[Dict[str, str]] = Field(
        ..., description="List of charts with name and base64 data"
    )
    summary: Optional[str] = Field(
        default="", description="Optional text summary of the analysis"
    )
