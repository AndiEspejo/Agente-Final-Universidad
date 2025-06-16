"""
Inventory-related Pydantic models for the sales/inventory system.

This module defines the core data structures for managing products,
inventory items, and related business logic with comprehensive validation.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional

from pydantic import Field, field_validator, model_validator

from src.models.base import BaseEntity


class ProductCategory(str, Enum):
    """Product categories supported by the system."""

    ELECTRONICS = "Electronics"
    FURNITURE = "Furniture"
    APPLIANCES = "Appliances"
    CLOTHING = "Clothing"
    BOOKS = "Books"
    SPORTS = "Sports"
    AUTOMOTIVE = "Automotive"
    FOOD = "Food"
    OTHER = "Other"


class ProductStatus(str, Enum):
    """Product status in the system."""

    ACTIVE = "active"
    DISCONTINUED = "discontinued"
    OUT_OF_STOCK = "out_of_stock"
    PENDING = "pending"


class Product(BaseEntity):
    """
    Product model representing items that can be sold.

    This model defines the core attributes of a product including
    pricing, categorization, and descriptive information.
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Product name, must be unique and descriptive",
    )

    sku: str = Field(
        ...,
        min_length=3,
        max_length=50,
        pattern=r"^[A-Z0-9\-]+$",
        description="Stock Keeping Unit - unique product identifier",
    )

    price: Decimal = Field(
        ...,
        gt=0,
        max_digits=10,
        decimal_places=2,
        description="Product price in the system's base currency",
    )

    cost: Optional[Decimal] = Field(
        None,
        ge=0,
        max_digits=10,
        decimal_places=2,
        description="Product cost for profit margin calculations",
    )

    category: ProductCategory = Field(
        ..., description="Product category for organization and filtering"
    )

    description: Optional[str] = Field(
        None, max_length=1000, description="Detailed product description for customers"
    )

    brand: Optional[str] = Field(
        None, max_length=100, description="Product brand or manufacturer"
    )

    supplier: Optional[str] = Field(
        None, max_length=100, description="Primary supplier for this product"
    )

    status: ProductStatus = Field(
        default=ProductStatus.ACTIVE,
        description="Current status of the product in the system",
    )

    weight: Optional[Decimal] = Field(
        None,
        ge=0,
        max_digits=8,
        decimal_places=3,
        description="Product weight in kilograms",
    )

    dimensions: Optional[Dict[str, float]] = Field(
        None, description="Product dimensions (length, width, height) in centimeters"
    )

    tags: List[str] = Field(
        default_factory=list, description="Product tags for search and categorization"
    )

    @field_validator("sku")
    @classmethod
    def validate_sku_format(cls, v):
        """Ensure SKU follows proper format conventions."""
        if not v:
            raise ValueError("SKU cannot be empty")

        # Check for valid characters and format
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError(
                "SKU must contain only alphanumeric characters, hyphens, and underscores"
            )

        return v.upper()

    @field_validator("price", "cost")
    @classmethod
    def validate_monetary_values(cls, v):
        """Ensure monetary values are properly formatted."""
        if v is not None and v < 0:
            raise ValueError("Monetary values cannot be negative")
        return v

    @field_validator("dimensions")
    @classmethod
    def validate_dimensions(cls, v):
        """Validate product dimensions format."""
        if v is not None:
            required_keys = {"length", "width", "height"}
            if not all(key in v for key in required_keys):
                raise ValueError("Dimensions must include length, width, and height")

            for key, value in v.items():
                if not isinstance(value, (int, float)) or value < 0:
                    raise ValueError(f"Dimension {key} must be a positive number")

        return v

    @model_validator(mode="after")
    def validate_cost_price_relationship(self):
        """Ensure cost is not greater than price."""
        if self.cost is not None and self.price is not None and self.cost > self.price:
            raise ValueError("Product cost cannot exceed the selling price")
        return self

    @property
    def profit_margin(self) -> Optional[Decimal]:
        """Calculate profit margin percentage."""
        if self.cost is not None and self.price > 0:
            return ((self.price - self.cost) / self.price) * 100
        return None

    @property
    def is_profitable(self) -> bool:
        """Check if the product is profitable."""
        return self.profit_margin is not None and self.profit_margin > 0


class InventoryLocation(str, Enum):
    """Available inventory storage locations."""

    WAREHOUSE_A = "Warehouse A"
    WAREHOUSE_B = "Warehouse B"
    WAREHOUSE_C = "Warehouse C"
    RETAIL_STORE = "Retail Store"
    DISTRIBUTION_CENTER = "Distribution Center"


class InventoryStatus(str, Enum):
    """Inventory item status."""

    IN_STOCK = "in_stock"
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"
    RESERVED = "reserved"
    DAMAGED = "damaged"


class InventoryItem(BaseEntity):
    """
    Inventory item model representing stock levels and location data.

    This model tracks the actual inventory quantities, locations,
    and stock management thresholds for products.
    """

    product_id: int = Field(
        ..., gt=0, description="Reference to the product this inventory item represents"
    )

    quantity: int = Field(
        ..., ge=0, description="Current quantity available in inventory"
    )

    reserved_quantity: int = Field(
        default=0, ge=0, description="Quantity reserved for pending orders"
    )

    min_threshold: int = Field(
        ..., ge=0, description="Minimum quantity threshold for low stock alerts"
    )

    max_threshold: int = Field(
        ..., gt=0, description="Maximum quantity threshold for reorder management"
    )

    reorder_point: Optional[int] = Field(
        None, ge=0, description="Quantity level that triggers automatic reorder"
    )

    reorder_quantity: Optional[int] = Field(
        None, gt=0, description="Quantity to order when reorder point is reached"
    )

    location: InventoryLocation = Field(
        ..., description="Physical location where inventory is stored"
    )

    bin_location: Optional[str] = Field(
        None,
        max_length=50,
        description="Specific bin or shelf location within the warehouse",
    )

    last_restocked: Optional[datetime] = Field(
        None, description="Timestamp of the last restocking operation"
    )

    last_counted: Optional[datetime] = Field(
        None, description="Timestamp of the last physical inventory count"
    )

    expiration_date: Optional[datetime] = Field(
        None, description="Expiration date for perishable items"
    )

    batch_number: Optional[str] = Field(
        None, max_length=100, description="Batch or lot number for tracking purposes"
    )

    notes: Optional[str] = Field(
        None, max_length=500, description="Additional notes about this inventory item"
    )

    @model_validator(mode="after")
    def validate_max_threshold(self):
        """Ensure max threshold is greater than min threshold."""
        if self.max_threshold <= self.min_threshold:
            raise ValueError("Maximum threshold must be greater than minimum threshold")
        return self

    @model_validator(mode="after")
    def validate_reserved_quantity(self):
        """Ensure reserved quantity doesn't exceed available quantity."""
        if self.reserved_quantity > self.quantity:
            raise ValueError("Reserved quantity cannot exceed available quantity")
        return self

    @model_validator(mode="after")
    def validate_reorder_point(self):
        """Ensure reorder point is logical."""
        if self.reorder_point is not None and self.reorder_point < self.min_threshold:
            raise ValueError("Reorder point should not be less than minimum threshold")
        return self

    @field_validator("expiration_date")
    @classmethod
    def validate_expiration_date(cls, v):
        """Ensure expiration date is in the future."""
        if v is not None and v <= datetime.now():
            raise ValueError("Expiration date must be in the future")
        return v

    @property
    def available_quantity(self) -> int:
        """Calculate available quantity (total - reserved)."""
        return max(0, self.quantity - self.reserved_quantity)

    @property
    def status(self) -> InventoryStatus:
        """Determine current inventory status based on quantity levels."""
        available = self.available_quantity

        if available == 0:
            return InventoryStatus.OUT_OF_STOCK
        elif available <= self.min_threshold:
            return InventoryStatus.LOW_STOCK
        elif self.reserved_quantity > 0:
            return InventoryStatus.RESERVED
        else:
            return InventoryStatus.IN_STOCK

    @property
    def needs_reorder(self) -> bool:
        """Check if this item needs to be reordered."""
        if self.reorder_point is None:
            return self.available_quantity <= self.min_threshold
        return self.available_quantity <= self.reorder_point

    @property
    def is_expired(self) -> bool:
        """Check if the item has expired."""
        if self.expiration_date is None:
            return False
        return datetime.now() > self.expiration_date

    @property
    def days_until_expiration(self) -> Optional[int]:
        """Calculate days until expiration."""
        if self.expiration_date is None:
            return None
        delta = self.expiration_date - datetime.now()
        return max(0, delta.days)


class StockMovementType(str, Enum):
    """Types of stock movements in the system."""

    INBOUND = "inbound"  # Stock received
    OUTBOUND = "outbound"  # Stock sold/shipped
    ADJUSTMENT = "adjustment"  # Inventory adjustment
    TRANSFER = "transfer"  # Location transfer
    RETURN = "return"  # Customer return
    DAMAGE = "damage"  # Damaged goods
    THEFT = "theft"  # Theft/loss


class StockMovement(BaseEntity):
    """
    Stock movement model for tracking inventory changes.

    This model records all inventory transactions including
    receipts, sales, transfers, and adjustments.
    """

    inventory_item_id: int = Field(
        ..., gt=0, description="Reference to the inventory item being moved"
    )

    movement_type: StockMovementType = Field(
        ..., description="Type of stock movement being recorded"
    )

    quantity: int = Field(
        ..., description="Quantity moved (positive for inbound, negative for outbound)"
    )

    reference_id: Optional[str] = Field(
        None, max_length=100, description="Reference to related document (PO, SO, etc.)"
    )

    from_location: Optional[InventoryLocation] = Field(
        None, description="Source location for transfers"
    )

    to_location: Optional[InventoryLocation] = Field(
        None, description="Destination location for transfers"
    )

    reason: Optional[str] = Field(
        None, max_length=200, description="Reason for the stock movement"
    )

    performed_by: Optional[str] = Field(
        None, max_length=100, description="User who performed the movement"
    )

    notes: Optional[str] = Field(
        None, max_length=500, description="Additional notes about the movement"
    )

    @model_validator(mode="after")
    def validate_quantity_sign(self):
        """Validate quantity sign based on movement type."""
        if self.movement_type in [StockMovementType.INBOUND, StockMovementType.RETURN]:
            if self.quantity <= 0:
                raise ValueError(
                    f"{self.movement_type} movements must have positive quantity"
                )
        elif self.movement_type in [
            StockMovementType.OUTBOUND,
            StockMovementType.DAMAGE,
            StockMovementType.THEFT,
        ]:
            if self.quantity >= 0:
                raise ValueError(
                    f"{self.movement_type} movements must have negative quantity"
                )
        return self

    @model_validator(mode="after")
    def validate_transfer_locations(self):
        """Validate location requirements for transfer movements."""
        if self.movement_type == StockMovementType.TRANSFER:
            if not self.from_location or not self.to_location:
                raise ValueError(
                    "Transfer movements require both from and to locations"
                )
            if self.from_location == self.to_location:
                raise ValueError("Transfer source and destination must be different")
        return self
