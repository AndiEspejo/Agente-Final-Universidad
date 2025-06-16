"""
Pydantic models for the sales/inventory system.

This package contains all data models used throughout the application
including base models, inventory models, and sales models.
"""

# Base models
from .base import APIResponse, BaseEntity, PaginationParams

# Inventory models
from .inventory import (
    InventoryItem,
    InventoryLocation,
    InventoryStatus,
    Product,
    ProductCategory,
    ProductStatus,
    StockMovement,
    StockMovementType,
)

# Sales models
from .sales import (
    Customer,
    CustomerStatus,
    CustomerType,
    OrderItem,
    OrderStatus,
    PaymentMethod,
    PaymentStatus,
    SalesOrder,
    SalesTransaction,
)


__all__ = [
    # Base models
    "BaseEntity",
    "APIResponse",
    "PaginationParams",
    # Inventory models
    "ProductCategory",
    "ProductStatus",
    "Product",
    "InventoryLocation",
    "InventoryStatus",
    "InventoryItem",
    "StockMovementType",
    "StockMovement",
    # Sales models
    "CustomerType",
    "CustomerStatus",
    "Customer",
    "OrderStatus",
    "PaymentStatus",
    "PaymentMethod",
    "SalesOrder",
    "OrderItem",
    "SalesTransaction",
]
