"""
Basic initialization utilities for the LangGraph Sales/Inventory System.
"""

from decimal import Decimal
from typing import List

from src.models.inventory import Product
from src.models.sales import Customer


def create_default_admin_user():
    """Create default admin user data."""
    return {
        "username": "admin",
        "full_name": "Administrator",
        "email": "admin@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # admin123
    }


def create_sample_products(count: int = 5) -> List[Product]:
    """Create a minimal set of sample products for initialization."""
    products = []

    sample_data = [
        {"name": "Laptop", "category": "Electronics", "price": 999.99},
        {"name": "Office Chair", "category": "Furniture", "price": 199.99},
        {"name": "Coffee Maker", "category": "Appliances", "price": 89.99},
        {"name": "Notebook", "category": "Other", "price": 4.99},
        {"name": "Wireless Mouse", "category": "Electronics", "price": 29.99},
    ]

    for i in range(min(count, len(sample_data))):
        data = sample_data[i]
        product = Product(
            id=i + 1,
            name=data["name"],
            description=f"Sample {data['name'].lower()}",
            category=data["category"],
            price=Decimal(str(data["price"])),
            sku=f"SKU-{i + 1:03d}",
        )
        products.append(product)

    return products


def create_sample_customers(count: int = 3) -> List[Customer]:
    """Create a minimal set of sample customers for initialization."""
    customers = []

    sample_data = [
        {"name": "John Doe", "email": "john@example.com"},
        {"name": "Jane Smith", "email": "jane@example.com"},
        {"name": "Bob Johnson", "email": "bob@example.com"},
    ]

    for i in range(min(count, len(sample_data))):
        data = sample_data[i]
        customer = Customer(
            id=i + 1,
            customer_code=f"CUST-{i + 1:03d}",
            name=data["name"],
            email=data["email"],
            customer_type="individual",
            phone=f"+1-555-{1000 + i}",
            credit_limit=Decimal("1000.00"),
            total_purchases=Decimal("0.00"),
        )
        customers.append(customer)

    return customers
