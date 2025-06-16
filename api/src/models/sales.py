"""
Sales-related Pydantic models for the sales/inventory system.

This module defines the core data structures for managing customers,
orders, sales transactions, and related business logic.
"""

import re
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, Optional

from pydantic import EmailStr, Field, field_validator, model_validator

from src.models.base import BaseEntity


class CustomerType(str, Enum):
    """Customer type classification."""

    INDIVIDUAL = "individual"
    BUSINESS = "business"
    GOVERNMENT = "government"
    NON_PROFIT = "non_profit"


class CustomerStatus(str, Enum):
    """Customer status in the system."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    VIP = "vip"


class Customer(BaseEntity):
    """
    Customer model representing individuals or organizations that purchase products.

    This model contains comprehensive customer information including
    contact details, preferences, and business relationship data.
    """

    customer_code: str = Field(
        ...,
        min_length=3,
        max_length=20,
        pattern=r"^[A-Z0-9\-]+$",
        description="Unique customer identifier code",
    )

    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Customer full name or company name",
    )

    customer_type: CustomerType = Field(
        ..., description="Type of customer (individual, business, etc.)"
    )

    email: EmailStr = Field(..., description="Primary email address for communication")

    phone: Optional[str] = Field(
        None, max_length=20, description="Primary phone number"
    )

    mobile: Optional[str] = Field(
        None, max_length=20, description="Mobile phone number"
    )

    status: CustomerStatus = Field(
        default=CustomerStatus.ACTIVE, description="Current status of the customer"
    )

    credit_limit: Optional[Decimal] = Field(
        None,
        ge=0,
        max_digits=12,
        decimal_places=2,
        description="Maximum credit limit for this customer",
    )

    current_balance: Decimal = Field(
        default=0,
        max_digits=12,
        decimal_places=2,
        description="Current outstanding balance",
    )

    discount_percentage: Decimal = Field(
        default=0,
        ge=0,
        le=100,
        max_digits=5,
        decimal_places=2,
        description="Default discount percentage for this customer",
    )

    tax_id: Optional[str] = Field(
        None, max_length=50, description="Tax identification number"
    )

    company_registration: Optional[str] = Field(
        None,
        max_length=50,
        description="Company registration number for business customers",
    )

    customer_since: date = Field(
        default_factory=date.today,
        description="Date when customer relationship started",
    )

    last_purchase_date: Optional[datetime] = Field(
        None, description="Date of the last purchase"
    )

    total_purchases: Decimal = Field(
        default=0,
        ge=0,
        max_digits=15,
        decimal_places=2,
        description="Total lifetime purchase amount",
    )

    purchase_count: int = Field(
        default=0, ge=0, description="Total number of purchases made"
    )

    preferred_payment_method: Optional[str] = Field(
        None, max_length=50, description="Customer's preferred payment method"
    )

    notes: Optional[str] = Field(
        None, max_length=1000, description="Additional notes about the customer"
    )

    @field_validator("customer_code")
    @classmethod
    def validate_customer_code(cls, v):
        """Ensure customer code follows proper format."""
        return v.upper()

    @field_validator("phone", "mobile")
    @classmethod
    def validate_phone_format(cls, v):
        """Validate phone number format."""
        if v is not None:
            # Remove spaces and common separators
            clean_phone = re.sub(r"[\s\-\(\)]+", "", v)
            # Check if it contains only digits and + for international
            if not re.match(r"^\+?[0-9]+$", clean_phone):
                raise ValueError(
                    "Phone number must contain only digits and optional leading +"
                )
            if len(clean_phone) < 7 or len(clean_phone) > 15:
                raise ValueError("Phone number must be between 7 and 15 digits")
        return v

    @model_validator(mode="after")
    def validate_credit_limit_constraint(self):
        """Ensure current balance doesn't exceed credit limit."""
        if self.credit_limit is not None and self.current_balance > self.credit_limit:
            raise ValueError("Current balance cannot exceed credit limit")
        return self

    @model_validator(mode="after")
    def validate_business_fields(self):
        """Validate business-specific fields for business customers."""
        if (
            self.customer_type == CustomerType.BUSINESS
            and not self.company_registration
        ):
            raise ValueError(
                "Business customers must have a company registration number"
            )
        return self

    @property
    def average_purchase_amount(self) -> Decimal:
        """Calculate average purchase amount."""
        if self.purchase_count > 0:
            return self.total_purchases / self.purchase_count
        return Decimal("0")

    @property
    def available_credit(self) -> Optional[Decimal]:
        """Calculate available credit limit."""
        if self.credit_limit is not None:
            return max(0, self.credit_limit - self.current_balance)
        return None

    @property
    def is_vip(self) -> bool:
        """Check if customer qualifies as VIP based on purchases."""
        return self.status == CustomerStatus.VIP or self.total_purchases > 10000


class OrderStatus(str, Enum):
    """Order status throughout the sales process."""

    DRAFT = "draft"
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    RETURNED = "returned"


class PaymentStatus(str, Enum):
    """Payment status for orders."""

    PENDING = "pending"
    AUTHORIZED = "authorized"
    PAID = "paid"
    PARTIALLY_PAID = "partially_paid"
    REFUNDED = "refunded"
    FAILED = "failed"


class PaymentMethod(str, Enum):
    """Available payment methods."""

    CASH = "cash"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    BANK_TRANSFER = "bank_transfer"
    CHECK = "check"
    DIGITAL_WALLET = "digital_wallet"
    CRYPTOCURRENCY = "cryptocurrency"
    STORE_CREDIT = "store_credit"


class SalesOrder(BaseEntity):
    """
    Sales order model representing customer purchase orders.

    This model captures the complete order information including
    customer details, order items, pricing, and fulfillment status.
    """

    order_number: str = Field(
        ..., min_length=3, max_length=50, description="Unique order number for tracking"
    )

    customer_id: int = Field(
        ..., gt=0, description="Reference to the customer placing the order"
    )

    order_date: datetime = Field(
        default_factory=datetime.now,
        description="Date and time when the order was placed",
    )

    required_date: Optional[datetime] = Field(
        None, description="Customer's requested delivery date"
    )

    shipped_date: Optional[datetime] = Field(
        None, description="Date when the order was shipped"
    )

    status: OrderStatus = Field(
        default=OrderStatus.DRAFT, description="Current status of the order"
    )

    payment_status: PaymentStatus = Field(
        default=PaymentStatus.PENDING, description="Payment status of the order"
    )

    payment_method: Optional[PaymentMethod] = Field(
        None, description="Method of payment for this order"
    )

    subtotal: Decimal = Field(
        default=0,
        ge=0,
        max_digits=12,
        decimal_places=2,
        description="Order subtotal before taxes and discounts",
    )

    discount_amount: Decimal = Field(
        default=0,
        ge=0,
        max_digits=10,
        decimal_places=2,
        description="Total discount applied to the order",
    )

    tax_amount: Decimal = Field(
        default=0,
        ge=0,
        max_digits=10,
        decimal_places=2,
        description="Total tax amount for the order",
    )

    shipping_cost: Decimal = Field(
        default=0,
        ge=0,
        max_digits=8,
        decimal_places=2,
        description="Shipping cost for the order",
    )

    total_amount: Decimal = Field(
        ...,
        ge=0,
        max_digits=12,
        decimal_places=2,
        description="Final total amount for the order",
    )

    shipping_address: Optional[Dict[str, str]] = Field(
        None, description="Shipping address information"
    )

    billing_address: Optional[Dict[str, str]] = Field(
        None, description="Billing address information"
    )

    notes: Optional[str] = Field(
        None,
        max_length=1000,
        description="Additional notes or instructions for the order",
    )

    sales_person: Optional[str] = Field(
        None, max_length=100, description="Sales person responsible for this order"
    )

    @model_validator(mode="after")
    def validate_dates(self):
        """Validate order dates are logical."""
        if self.required_date is not None and self.required_date < self.order_date:
            raise ValueError("Required date cannot be before order date")
        if self.shipped_date is not None and self.shipped_date < self.order_date:
            raise ValueError("Shipped date cannot be before order date")
        return self

    @field_validator("shipping_address", "billing_address")
    @classmethod
    def validate_address_format(cls, v):
        """Validate address dictionary format."""
        if v is not None:
            required_fields = {"street", "city", "postal_code", "country"}
            if not all(field in v for field in required_fields):
                raise ValueError(
                    "Address must include street, city, postal_code, and country"
                )
        return v

    @model_validator(mode="after")
    def validate_total_calculation(self):
        """Validate that total amount calculation is correct."""
        calculated_total = (
            self.subtotal - self.discount_amount + self.tax_amount + self.shipping_cost
        )

        # Allow for small rounding differences
        if abs(self.total_amount - calculated_total) > Decimal("0.01"):
            raise ValueError(
                "Total amount must equal subtotal - discount + tax + shipping"
            )

        return self

    @property
    def is_overdue(self) -> bool:
        """Check if the order is overdue based on required date."""
        if self.required_date is None:
            return False
        return datetime.now() > self.required_date and self.status not in [
            OrderStatus.DELIVERED,
            OrderStatus.CANCELLED,
        ]

    @property
    def can_be_cancelled(self) -> bool:
        """Check if the order can still be cancelled."""
        return self.status in [
            OrderStatus.DRAFT,
            OrderStatus.PENDING,
            OrderStatus.CONFIRMED,
        ]


class OrderItem(BaseEntity):
    """
    Order item model representing individual products within an order.

    This model captures the specific products, quantities, and pricing
    for each line item in a sales order.
    """

    order_id: int = Field(..., gt=0, description="Reference to the parent sales order")

    product_id: int = Field(
        ..., gt=0, description="Reference to the product being ordered"
    )

    quantity: int = Field(..., gt=0, description="Quantity of the product ordered")

    unit_price: Decimal = Field(
        ...,
        gt=0,
        max_digits=10,
        decimal_places=2,
        description="Price per unit at the time of order",
    )

    line_discount: Decimal = Field(
        default=0,
        ge=0,
        max_digits=8,
        decimal_places=2,
        description="Discount applied to this line item",
    )

    line_total: Decimal = Field(
        ...,
        ge=0,
        max_digits=12,
        decimal_places=2,
        description="Total amount for this line item",
    )

    notes: Optional[str] = Field(
        None, max_length=500, description="Notes specific to this order item"
    )

    @model_validator(mode="after")
    def validate_line_total(self):
        """Validate line total calculation."""
        calculated_total = (self.quantity * self.unit_price) - self.line_discount

        if abs(self.line_total - calculated_total) > Decimal("0.01"):
            raise ValueError("Line total must equal (quantity × unit_price) - discount")

        return self


class SalesTransaction(BaseEntity):
    """
    Sales transaction model for recording completed sales.

    This model represents the final recorded sale with payment
    information and transaction details.
    """

    transaction_number: str = Field(
        ..., min_length=3, max_length=50, description="Unique transaction identifier"
    )

    order_id: Optional[int] = Field(
        None, gt=0, description="Reference to the originating sales order"
    )

    customer_id: int = Field(..., gt=0, description="Reference to the customer")

    transaction_date: datetime = Field(
        default_factory=datetime.now, description="Date and time of the transaction"
    )

    payment_method: PaymentMethod = Field(..., description="Method used for payment")

    amount_paid: Decimal = Field(
        ...,
        gt=0,
        max_digits=12,
        decimal_places=2,
        description="Amount paid by the customer",
    )

    change_given: Decimal = Field(
        default=0,
        ge=0,
        max_digits=8,
        decimal_places=2,
        description="Change given to the customer",
    )

    payment_reference: Optional[str] = Field(
        None,
        max_length=100,
        description="External payment reference (transaction ID, check number, etc.)",
    )

    processed_by: Optional[str] = Field(
        None, max_length=100, description="Staff member who processed the transaction"
    )

    notes: Optional[str] = Field(
        None, max_length=500, description="Additional transaction notes"
    )

    @property
    def is_cash_transaction(self) -> bool:
        """Check if this is a cash transaction."""
        return self.payment_method == PaymentMethod.CASH

    @property
    def net_amount(self) -> Decimal:
        """Calculate net amount (paid - change)."""
        return self.amount_paid - self.change_given
