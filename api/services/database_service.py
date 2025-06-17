"""
Database service layer for CRUD operations.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.api_models import ProductCreateRequest, ProductEditRequest
from models.database_models import (
    Customer,
    InventoryItem,
    Order,
    OrderItem,
    Product,
)


class DatabaseService:
    """Service class for database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # PRODUCT OPERATIONS
    async def create_product(self, product_data: ProductCreateRequest) -> Product:
        """Create a new product."""
        product = Product(
            name=product_data.name,
            description=product_data.description or "",
            category=product_data.category or "Other",
            price=float(product_data.price),
            sku=product_data.sku
            or f"SKU-{datetime.now().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:8]}",
            unit_cost=float(product_data.unit_cost) if product_data.unit_cost else None,
        )

        self.session.add(product)
        await self.session.flush()  # Get the ID

        # Create corresponding inventory item
        inventory_item = InventoryItem(
            product_id=product.id,
            quantity=product_data.quantity,
            min_threshold=product_data.minimum_stock
            or max(5, product_data.quantity // 5),
            max_threshold=product_data.maximum_stock or product_data.quantity * 2,
            location="Almacén Principal",
        )

        self.session.add(inventory_item)
        return product

    async def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """Get product by ID with inventory information."""
        result = await self.session.execute(
            select(Product)
            .options(selectinload(Product.inventory_items))
            .where(Product.id == product_id)
        )
        return result.scalars().first()

    async def get_all_products(self) -> List[Product]:
        """Get all products with inventory information."""
        result = await self.session.execute(
            select(Product).options(selectinload(Product.inventory_items))
        )
        return result.scalars().all()

    async def update_product(
        self, product_id: int, update_data: ProductEditRequest
    ) -> Optional[Product]:
        """Update product information."""
        # Update product
        product_updates = {}
        if update_data.name is not None:
            product_updates["name"] = update_data.name
        if update_data.price is not None:
            product_updates["price"] = float(update_data.price)
        if update_data.category is not None:
            product_updates["category"] = update_data.category
        if update_data.description is not None:
            product_updates["description"] = update_data.description

        if product_updates:
            product_updates["updated_at"] = datetime.utcnow()
            await self.session.execute(
                update(Product)
                .where(Product.id == product_id)
                .values(**product_updates)
            )

        # Update inventory if needed
        inventory_updates = {}
        if update_data.quantity is not None:
            inventory_updates["quantity"] = update_data.quantity
        if update_data.minimum_stock is not None:
            inventory_updates["min_threshold"] = update_data.minimum_stock
        if update_data.maximum_stock is not None:
            inventory_updates["max_threshold"] = update_data.maximum_stock

        if inventory_updates:
            inventory_updates["last_updated"] = datetime.utcnow()
            await self.session.execute(
                update(InventoryItem)
                .where(InventoryItem.product_id == product_id)
                .values(**inventory_updates)
            )

        return await self.get_product_by_id(product_id)

    async def delete_product(self, product_id: int) -> bool:
        """Delete a product and its inventory items."""
        result = await self.session.execute(
            delete(Product).where(Product.id == product_id)
        )
        return result.rowcount > 0

    # INVENTORY OPERATIONS
    async def get_products_with_stock(self) -> List[Dict[str, Any]]:
        """Get all products with their current stock information."""
        result = await self.session.execute(
            select(Product, InventoryItem).join(
                InventoryItem, Product.id == InventoryItem.product_id
            )
        )

        products_with_stock = []
        for product, inventory in result.all():
            products_with_stock.append(
                {
                    "id": product.id,
                    "name": product.name,
                    "sku": product.sku,
                    "price": float(product.price),
                    "category": product.category,
                    "stock_quantity": inventory.quantity,
                    "stock_status": inventory.status,
                    "location": inventory.location,
                    "available_for_sale": inventory.quantity > 0,
                }
            )

        return products_with_stock

    async def update_stock(
        self, product_id: int, new_quantity: int
    ) -> Optional[InventoryItem]:
        """Update stock quantity for a product."""
        await self.session.execute(
            update(InventoryItem)
            .where(InventoryItem.product_id == product_id)
            .values(quantity=new_quantity, last_updated=datetime.utcnow())
        )

        result = await self.session.execute(
            select(InventoryItem).where(InventoryItem.product_id == product_id)
        )
        return result.scalars().first()

    async def get_inventory_summary(self) -> Dict[str, Any]:
        """Get inventory summary statistics."""
        # Count total products
        total_products_result = await self.session.execute(
            select(func.count(Product.id))
        )
        total_products = total_products_result.scalar()

        # Count total inventory items and sum quantities
        inventory_stats = await self.session.execute(
            select(func.count(InventoryItem.id), func.sum(InventoryItem.quantity))
        )
        total_items, total_units = inventory_stats.first()

        # Count low stock items (quantity <= min_threshold)
        low_stock_result = await self.session.execute(
            select(func.count(InventoryItem.id)).where(
                InventoryItem.quantity <= InventoryItem.min_threshold
            )
        )
        low_stock_items = low_stock_result.scalar()

        return {
            "total_products": total_products or 0,
            "total_items": total_items or 0,
            "total_units": total_units or 0,
            "low_stock_items": low_stock_items or 0,
        }

    # CUSTOMER OPERATIONS
    async def create_customer(
        self,
        name: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        address: Optional[str] = None,
        customer_type: str = "individual",
    ) -> Customer:
        """Create a new customer."""
        customer = Customer(
            name=name,
            email=email,
            phone=phone,
            address=address,
            customer_type=customer_type,
        )
        self.session.add(customer)
        await self.session.flush()
        return customer

    async def get_customer_by_id(self, customer_id: int) -> Optional[Customer]:
        """Get customer by ID."""
        result = await self.session.execute(
            select(Customer).where(Customer.id == customer_id)
        )
        return result.scalars().first()

    async def get_all_customers(self) -> List[Customer]:
        """Get all customers."""
        result = await self.session.execute(select(Customer))
        return result.scalars().all()

    # ORDER OPERATIONS
    async def create_order(
        self,
        customer_id: int,
        items: List[Dict[str, Any]],
        payment_method: str = "tarjeta_debito",
    ) -> Order:
        """Create a new order with items."""
        order = Order(
            customer_id=customer_id, payment_method=payment_method, total_amount=0.0
        )
        self.session.add(order)
        await self.session.flush()  # Get order ID

        total_amount = 0.0
        for item_data in items:
            # Get product to get current price
            product = await self.get_product_by_id(item_data["product_id"])
            if not product:
                continue

            unit_price = item_data.get("price", product.price)
            quantity = item_data["quantity"]
            total_price = float(unit_price) * quantity

            order_item = OrderItem(
                order_id=order.id,
                product_id=item_data["product_id"],
                quantity=quantity,
                unit_price=float(unit_price),
                total_price=total_price,
            )
            self.session.add(order_item)
            total_amount += total_price

            # Update inventory
            await self.update_stock(
                item_data["product_id"], product.inventory_items[0].quantity - quantity
            )

        # Update order total
        order.total_amount = total_amount
        return order

    async def get_order_by_id(self, order_id: int) -> Optional[Order]:
        """Get order by ID with items."""
        result = await self.session.execute(
            select(Order)
            .options(selectinload(Order.order_items))
            .where(Order.id == order_id)
        )
        return result.scalars().first()

    async def get_all_orders(self) -> List[Order]:
        """Get all orders with items and customer info."""
        result = await self.session.execute(
            select(Order).options(
                selectinload(Order.order_items).selectinload(OrderItem.product),
                selectinload(Order.customer),
            )
        )
        return result.scalars().all()

    # UTILITY METHODS
    async def get_analytics_data(self) -> Dict[str, Any]:
        """Get data for analytics and reporting."""
        products = await self.get_all_products()
        orders = await self.get_all_orders()
        customers = await self.get_all_customers()
        inventory_summary = await self.get_inventory_summary()

        return {
            "products": [self._product_to_dict(p) for p in products],
            "orders": [self._order_to_dict(o) for o in orders],
            "customers": [self._customer_to_dict(c) for c in customers],
            "inventory": await self.get_products_with_stock(),
            "summary": inventory_summary,
        }

    def _product_to_dict(self, product: Product) -> Dict[str, Any]:
        """Convert Product model to dictionary."""
        return {
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "category": product.category,
            "price": float(product.price),
            "sku": product.sku,
            "unit_cost": float(product.unit_cost) if product.unit_cost else None,
            "created_at": (
                product.created_at.isoformat() if product.created_at else None
            ),
            "updated_at": (
                product.updated_at.isoformat() if product.updated_at else None
            ),
        }

    def _order_to_dict(self, order: Order) -> Dict[str, Any]:
        """Convert Order model to dictionary."""
        return {
            "id": order.id,
            "customer_id": order.customer_id,
            "status": order.status,
            "payment_method": order.payment_method,
            "total_amount": float(order.total_amount),
            "notes": order.notes,
            "order_date": order.order_date.isoformat() if order.order_date else None,
            "items": (
                [self._order_item_to_dict(item) for item in order.order_items]
                if order.order_items
                else []
            ),
        }

    def _order_item_to_dict(self, item: OrderItem) -> Dict[str, Any]:
        """Convert OrderItem model to dictionary."""
        return {
            "id": item.id,
            "product_id": item.product_id,
            "product_name": (
                item.product.name if item.product else f"Producto #{item.product_id}"
            ),
            "quantity": item.quantity,
            "unit_price": float(item.unit_price),
            "total_price": float(item.total_price),
        }

    def _customer_to_dict(self, customer: Customer) -> Dict[str, Any]:
        """Convert Customer model to dictionary."""
        return {
            "id": customer.id,
            "name": customer.name,
            "email": customer.email,
            "phone": customer.phone,
            "address": customer.address,
            "customer_type": customer.customer_type,
            "created_at": (
                customer.created_at.isoformat() if customer.created_at else None
            ),
        }
