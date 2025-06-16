"""
Database models for the Sales/Inventory System using SQLAlchemy.
"""

import enum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class InventoryLocation(str, enum.Enum):
    """Inventory location enum."""

    WAREHOUSE_A = "WAREHOUSE_A"
    WAREHOUSE_B = "WAREHOUSE_B"
    STORE_FRONT = "STORE_FRONT"
    SUPPLIER = "SUPPLIER"


class OrderStatus(str, enum.Enum):
    """Order status enum."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class User(Base):
    """User model for authentication."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    hashed_password = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Product(Base):
    """Product model."""

    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=False, default="Other")
    price = Column(Float, nullable=False)
    unit_cost = Column(Float, nullable=True)  # Costo unitario del producto
    sku = Column(String(100), unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    inventory_items = relationship(
        "InventoryItem", back_populates="product", cascade="all, delete-orphan"
    )
    order_items = relationship("OrderItem", back_populates="product")


class InventoryItem(Base):
    """Inventory item model."""

    __tablename__ = "inventory_items"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=0)
    min_threshold = Column(Integer, nullable=False, default=10)
    max_threshold = Column(Integer, nullable=False, default=100)
    location = Column(
        Enum(InventoryLocation), nullable=False, default=InventoryLocation.WAREHOUSE_A
    )
    last_updated = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    product = relationship("Product", back_populates="inventory_items")

    @property
    def status(self) -> str:
        """Calculate inventory status based on quantity and thresholds."""
        if self.quantity == 0:
            return "agotado"
        elif self.quantity <= self.min_threshold:
            return "crítico"
        elif self.quantity <= (self.min_threshold * 2):
            return "bajo"
        else:
            return "normal"


class Customer(Base):
    """Customer model."""

    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=True)
    phone = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    customer_type = Column(String(50), nullable=False, default="individual")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    orders = relationship("Order", back_populates="customer")


class Order(Base):
    """Sales order model."""

    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    status = Column(Enum(OrderStatus), nullable=False, default=OrderStatus.PENDING)
    payment_method = Column(String(50), nullable=False, default="credit_card")
    total_amount = Column(Float, nullable=False, default=0.0)
    notes = Column(Text, nullable=True)
    order_date = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    customer = relationship("Customer", back_populates="orders")
    order_items = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )


class OrderItem(Base):
    """Order item model (line items in an order)."""

    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    order = relationship("Order", back_populates="order_items")
    product = relationship("Product", back_populates="order_items")


class ChatLog(Base):
    """Chat interaction logging model."""

    __tablename__ = "chat_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    message = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    workflow_id = Column(String(100), nullable=True)
    processing_time = Column(Float, nullable=True)  # seconds
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User")
