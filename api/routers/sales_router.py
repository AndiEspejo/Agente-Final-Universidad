"""
Sales router for order management and sales analysis - Database Version.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from auth import User, get_current_active_user
from database import get_async_session
from models.api_models import ChatResponse, SalesOrderRequest
from models.database_models import OrderStatus
from services.database_service import DatabaseService


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sales", tags=["sales"])


@router.post("/create-order-with-inventory-sync")
async def create_order_with_inventory_sync(
    order_data: SalesOrderRequest,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Create a new sales order and automatically update inventory quantities.

    Expected format:
    {
        "customer_id": 1,
        "items": [
            {"product_id": 1, "quantity": 2},
            {"product_id": 3, "quantity": 1}
        ],
        "payment_method": "credit_card"
    }
    """
    try:
        logger.info(
            f"🛒 Creating new order with inventory sync for user: {current_user.username}"
        )

        db_service = DatabaseService(session)


        # Validate customer exists (create default if not)
        customer = await db_service.get_customer_by_id(order_data.customer_id)
        if not customer:
            # Create default customer
            customer = await db_service.create_customer(
                name="Cliente General", email="general@example.com"
            )
            order_data.customer_id = customer.id

        # Validate inventory availability and prepare order items
        items_data = order_data.items
        order_items_data = []
        total_amount = 0.0
        inventory_updates = []

        for item_data in items_data:
            product_id = item_data["product_id"]
            requested_qty = item_data["quantity"]

            # Get product with inventory
            product = await db_service.get_product_by_id(product_id)
            if not product:
                raise HTTPException(
                    status_code=400, detail=f"Producto ID {product_id} no encontrado"
                )

            # Check inventory availability
            if not product.inventory_items:
                raise HTTPException(
                    status_code=400,
                    detail=f"No hay inventario para el producto '{product.name}'",
                )

            inventory_item = product.inventory_items[0]
            current_stock = inventory_item.quantity

            if current_stock < requested_qty:
                raise HTTPException(
                    status_code=400,
                    detail=f"Stock insuficiente para '{product.name}'. "
                    f"Disponible: {current_stock}, Solicitado: {requested_qty}",
                )

            # Calculate pricing
            unit_price = float(product.price)
            item_total = unit_price * requested_qty
            total_amount += item_total

            # Prepare order item data
            order_items_data.append(
                {
                    "product_id": product_id,
                    "quantity": requested_qty,
                    "price": unit_price,  # Use current product price
                }
            )

            # Track inventory changes for response
            inventory_updates.append(
                {
                    "product_id": product_id,
                    "product_name": product.name,
                    "previous_quantity": current_stock,
                    "new_quantity": current_stock - requested_qty,
                    "quantity_sold": requested_qty,
                }
            )

        # Create the order with items
        order = await db_service.create_order(
            customer_id=order_data.customer_id,
            items=order_items_data,
            payment_method=order_data.payment_method,
        )

        # Build response
        order_items_text = "\n".join(
            [
                f"- **{update['product_name']}**: {update['quantity_sold']} unidades (Stock restante: {update['new_quantity']})"
                for update in inventory_updates
            ]
        )

        response_text = f"""✅ **¡Orden Creada Exitosamente!**

**Detalles de la Orden:**
- **ID de Orden:** {order.id}
- **Cliente ID:** {order.customer_id}
- **Método de Pago:** {order.payment_method}
- **Total:** ${order.total_amount:.2f}
- **Estado:** {order.status.value}

**Productos Vendidos:**
{order_items_text}

**Actualización de Inventario:**
Se ha actualizado automáticamente el stock de todos los productos vendidos.

¡La orden ha sido procesada exitosamente!"""

        return ChatResponse(
            response=response_text,
            data={
                "order_id": order.id,
                "customer_id": order.customer_id,
                "total_amount": float(order.total_amount),
                "payment_method": order.payment_method,
                "status": order.status.value,
                "inventory_updates": inventory_updates,
                "items_count": len(order_items_data),
            },
            workflow_id=f"create-order-{order.id}",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating order: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creando orden: {str(e)}")


@router.get("/list")
async def list_orders(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """List all sales orders."""
    try:
        db_service = DatabaseService(session)
        orders = await db_service.get_all_orders()

        orders_data = []
        for order in orders:
            orders_data.append(
                {
                    "id": order.id,
                    "customer_id": order.customer_id,
                    "customer_name": (
                        order.customer.name if order.customer else "Cliente Desconocido"
                    ),
                    "status": order.status.value,
                    "payment_method": order.payment_method,
                    "total_amount": float(order.total_amount),
                    "order_date": (
                        order.order_date.isoformat() if order.order_date else None
                    ),
                    "items_count": len(order.order_items) if order.order_items else 0,
                }
            )

        return {
            "orders": orders_data,
            "total_orders": len(orders_data),
            "total_value": sum(float(order.total_amount) for order in orders),
        }

    except Exception as e:
        logger.error(f"Error listing orders: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error obteniendo órdenes: {str(e)}"
        )


@router.get("/order/{order_id}")
async def get_order_details(
    order_id: int,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Get detailed information about a specific order."""
    try:
        db_service = DatabaseService(session)
        order = await db_service.get_order_by_id(order_id)

        if not order:
            raise HTTPException(
                status_code=404, detail=f"Orden con ID {order_id} no encontrada"
            )

        # Get order items with product details
        order_items = []
        for item in order.order_items:
            product = await db_service.get_product_by_id(item.product_id)
            order_items.append(
                {
                    "id": item.id,
                    "product_id": item.product_id,
                    "product_name": product.name if product else "Producto Desconocido",
                    "product_sku": product.sku if product else "N/A",
                    "quantity": item.quantity,
                    "unit_price": float(item.unit_price),
                    "total_price": float(item.total_price),
                }
            )

        return {
            "order": {
                "id": order.id,
                "customer_id": order.customer_id,
                "customer_name": (
                    order.customer.name if order.customer else "Cliente Desconocido"
                ),
                "status": order.status.value,
                "payment_method": order.payment_method,
                "total_amount": float(order.total_amount),
                "order_date": (
                    order.order_date.isoformat() if order.order_date else None
                ),
                "notes": order.notes,
            },
            "items": order_items,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting order details: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error obteniendo detalles de orden: {str(e)}"
        )


@router.put("/order/{order_id}/status")
async def update_order_status(
    order_id: int,
    status: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Update the status of an order."""
    try:
        db_service = DatabaseService(session)

        # Validate status
        try:
            new_status = OrderStatus(status)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Estado inválido: {status}. Estados válidos: {[s.value for s in OrderStatus]}",
            )

        # Get and update order
        order = await db_service.get_order_by_id(order_id)
        if not order:
            raise HTTPException(
                status_code=404, detail=f"Orden con ID {order_id} no encontrada"
            )

        old_status = order.status.value
        order.status = new_status

        return {
            "message": "Estado de orden actualizado exitosamente",
            "order_id": order_id,
            "old_status": old_status,
            "new_status": status,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating order status: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error actualizando estado: {str(e)}"
        )


@router.get("/customers")
async def list_customers(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """List all customers."""
    try:
        db_service = DatabaseService(session)
        customers = await db_service.get_all_customers()

        customers_data = []
        for customer in customers:
            customers_data.append(
                {
                    "id": customer.id,
                    "name": customer.name,
                    "email": customer.email,
                    "phone": customer.phone,
                    "customer_type": customer.customer_type,
                    "created_at": (
                        customer.created_at.isoformat() if customer.created_at else None
                    ),
                }
            )

        return {"customers": customers_data, "total_customers": len(customers_data)}

    except Exception as e:
        logger.error(f"Error listing customers: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error obteniendo clientes: {str(e)}"
        )


@router.post("/customer")
async def create_customer(
    customer_data: dict,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Create a new customer."""
    try:
        db_service = DatabaseService(session)

        customer = await db_service.create_customer(
            name=customer_data["name"],
            email=customer_data.get("email"),
            phone=customer_data.get("phone"),
            address=customer_data.get("address"),
            customer_type=customer_data.get("customer_type", "individual"),
        )

        return {
            "message": "Cliente creado exitosamente",
            "customer": {
                "id": customer.id,
                "name": customer.name,
                "email": customer.email,
                "phone": customer.phone,
                "customer_type": customer.customer_type,
            },
        }

    except Exception as e:
        logger.error(f"Error creating customer: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creando cliente: {str(e)}")


@router.get("/status")
async def get_sales_status(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Get sales system status and summary."""
    try:
        db_service = DatabaseService(session)

        orders = await db_service.get_all_orders()
        customers = await db_service.get_all_customers()

        # Calculate statistics
        total_sales = sum(float(order.total_amount) for order in orders)
        pending_orders = len(
            [order for order in orders if order.status == OrderStatus.PENDING]
        )
        confirmed_orders = len(
            [order for order in orders if order.status == OrderStatus.CONFIRMED]
        )

        return {
            "status": "healthy",
            "database_connected": True,
            "summary": {
                "total_orders": len(orders),
                "total_customers": len(customers),
                "total_sales": total_sales,
                "pending_orders": pending_orders,
                "confirmed_orders": confirmed_orders,
            },
            "system_info": {
                "version": "3.0.0 - Database Version",
                "features": [
                    "Database-powered orders",
                    "Real-time inventory sync",
                    "Customer management",
                    "Order status tracking",
                ],
            },
        }

    except Exception as e:
        logger.error(f"Error getting sales status: {str(e)}")
        return {"status": "error", "database_connected": False, "error": str(e)}


@router.get("/debug/data")
async def debug_sales_data(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Debug endpoint to view all sales data."""
    try:
        db_service = DatabaseService(session)

        analytics_data = await db_service.get_analytics_data()

        return {
            "database_info": {
                "total_products": len(analytics_data["products"]),
                "total_orders": len(analytics_data["orders"]),
                "total_customers": len(analytics_data["customers"]),
                "inventory_summary": analytics_data["summary"],
            },
            "data": analytics_data,
        }

    except Exception as e:
        logger.error(f"Error in debug endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error en debug: {str(e)}")
