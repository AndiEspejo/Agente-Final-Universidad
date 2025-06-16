"""
Inventory router for product and stock management - Database Version.
"""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from auth import User, get_current_active_user
from database import get_async_session
from models.api_models import (
    ChatResponse,
    ProductCreateRequest,
    ProductEditRequest,
    StockUpdateRequest,
)
from services.database_service import DatabaseService


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.post("/add-product", response_model=ChatResponse)
async def add_inventory_product(
    product_data: ProductCreateRequest,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Add a new product to inventory."""
    try:
        db_service = DatabaseService(session)

        # Check for duplicate names and SKUs
        existing_products = await db_service.get_all_products()
        proposed_sku = (
            product_data.sku or f"SKU-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        )

        for existing_product in existing_products:
            if (
                existing_product.name.lower().strip()
                == product_data.name.lower().strip()
            ):
                raise HTTPException(
                    status_code=400,
                    detail=f"❌ **Producto Duplicado**: Ya existe un producto con el nombre '{existing_product.name}'. "
                    f"Los nombres de productos deben ser únicos. Por favor, elige un nombre diferente.",
                )

            if existing_product.sku.upper() == proposed_sku.upper():
                raise HTTPException(
                    status_code=400,
                    detail=f"❌ **SKU Duplicado**: Ya existe un producto con el SKU '{existing_product.sku}'. "
                    f"Los SKUs deben ser únicos. Por favor, elige un SKU diferente.",
                )

        # Set the SKU
        product_data.sku = proposed_sku

        # Create product and inventory item
        product = await db_service.create_product(product_data)

        # Calculate total inventory units
        inventory_summary = await db_service.get_inventory_summary()

        response_text = f"""✅ **¡Producto Añadido al Inventario!**

**Detalles del Producto:**
- **Nombre:** {product.name}
- **SKU:** {product.sku}
- **Categoría:** {product.category}
- **Precio:** ${product.price:.2f}
- **Cantidad inicial:** {product_data.quantity} unidades
- **Stock mínimo:** {product_data.minimum_stock or max(5, product_data.quantity // 5)}
- **Stock máximo:** {product_data.maximum_stock or product_data.quantity * 2}

**Resumen del Inventario:**
- Total productos únicos: {inventory_summary["total_products"]}
- Total unidades en inventario: {inventory_summary["total_units"]}

¡El producto ha sido añadido exitosamente al sistema!"""

        return ChatResponse(
            response=response_text,
            data={
                "product_id": product.id,
                "product_name": product.name,
                "product_sku": product.sku,
                "inventory_summary": inventory_summary,
            },
            workflow_id=f"add-product-{product.id}",
        )

    except Exception as e:
        logger.error(f"Error adding product to inventory: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error añadiendo producto: {str(e)}"
        )


@router.get("/list")
async def list_inventory(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """List all inventory items with summary."""
    try:
        db_service = DatabaseService(session)

        products_with_stock = await db_service.get_products_with_stock()
        summary = await db_service.get_inventory_summary()

        return {"inventory": products_with_stock, "summary": summary}
    except Exception as e:
        logger.error(f"Error listing inventory: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error obteniendo inventario: {str(e)}"
        )


@router.post("/update-stock", response_model=ChatResponse)
async def update_inventory_stock(
    update_data: StockUpdateRequest,
    session: AsyncSession = Depends(get_async_session),
):
    """Update stock quantity for a product."""
    try:
        db_service = DatabaseService(session)

        # Get the product first
        product = await db_service.get_product_by_id(update_data.item_id)
        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"Producto con ID {update_data.item_id} no encontrado",
            )

        # Get old quantity
        old_quantity = (
            product.inventory_items[0].quantity if product.inventory_items else 0
        )

        # Update stock
        inventory_item = await db_service.update_stock(
            update_data.item_id, update_data.quantity
        )
        if not inventory_item:
            raise HTTPException(
                status_code=404,
                detail=f"Inventario para producto ID {update_data.item_id} no encontrado",
            )

        is_low_stock = update_data.quantity <= inventory_item.min_threshold

        response_text = f"""✅ **¡Stock Actualizado!**

**Producto:** {product.name}
**SKU:** {product.sku}
**Cantidad anterior:** {old_quantity}
**Cantidad nueva:** {update_data.quantity}
**Diferencia:** {update_data.quantity - old_quantity:+d}

{"⚠️ **ALERTA:** Stock por debajo del mínimo!" if is_low_stock else "✅ Stock adecuado"}"""

        return ChatResponse(
            response=response_text,
            data={
                "product_id": product.id,
                "product_name": product.name,
                "old_quantity": old_quantity,
                "new_quantity": update_data.quantity,
                "is_low_stock": is_low_stock,
                "stock_status": inventory_item.status,
            },
            workflow_id=f"update-stock-{update_data.item_id}",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating stock: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error actualizando stock: {str(e)}"
        )


@router.post("/edit-product", response_model=ChatResponse)
async def edit_inventory_product(
    edit_data: ProductEditRequest,
    session: AsyncSession = Depends(get_async_session),
):
    """Edit an existing product and its inventory information."""
    try:
        db_service = DatabaseService(session)

        # Check if product exists
        existing_product = await db_service.get_product_by_id(edit_data.product_id)
        if not existing_product:
            raise HTTPException(
                status_code=404,
                detail=f"❌ **Producto no encontrado**: No existe un producto con ID {edit_data.product_id}",
            )

        # Store old values for comparison
        old_values = {
            "name": existing_product.name,
            "price": existing_product.price,
            "category": existing_product.category,
            "description": existing_product.description or "",
            "quantity": (
                existing_product.inventory_items[0].quantity
                if existing_product.inventory_items
                else 0
            ),
            "min_threshold": (
                existing_product.inventory_items[0].min_threshold
                if existing_product.inventory_items
                else 0
            ),
            "max_threshold": (
                existing_product.inventory_items[0].max_threshold
                if existing_product.inventory_items
                else 0
            ),
        }

        # Update the product
        updated_product = await db_service.update_product(
            edit_data.product_id, edit_data
        )
        if not updated_product:
            raise HTTPException(
                status_code=500, detail="Error actualizando el producto"
            )

        # Build response showing changes
        changes = []
        if edit_data.name is not None and edit_data.name != old_values["name"]:
            changes.append(f"• **Nombre:** '{old_values['name']}' → '{edit_data.name}'")
        if edit_data.price is not None and float(edit_data.price) != float(
            old_values["price"]
        ):
            changes.append(
                f"• **Precio:** ${old_values['price']:.2f} → ${edit_data.price:.2f}"
            )
        if (
            edit_data.category is not None
            and edit_data.category != old_values["category"]
        ):
            changes.append(
                f"• **Categoría:** '{old_values['category']}' → '{edit_data.category}'"
            )
        if (
            edit_data.description is not None
            and edit_data.description != old_values["description"]
        ):
            changes.append("• **Descripción:** Actualizada")
        if (
            edit_data.quantity is not None
            and edit_data.quantity != old_values["quantity"]
        ):
            changes.append(
                f"• **Cantidad:** {old_values['quantity']} → {edit_data.quantity}"
            )
        if (
            edit_data.minimum_stock is not None
            and edit_data.minimum_stock != old_values["min_threshold"]
        ):
            changes.append(
                f"• **Stock mínimo:** {old_values['min_threshold']} → {edit_data.minimum_stock}"
            )
        if (
            edit_data.maximum_stock is not None
            and edit_data.maximum_stock != old_values["max_threshold"]
        ):
            changes.append(
                f"• **Stock máximo:** {old_values['max_threshold']} → {edit_data.maximum_stock}"
            )

        if not changes:
            changes_text = (
                "**No se realizaron cambios** (valores idénticos a los existentes)"
            )
        else:
            changes_text = "**Cambios realizados:**\n" + "\n".join(changes)

        # Get current inventory status
        current_inventory = (
            updated_product.inventory_items[0]
            if updated_product.inventory_items
            else None
        )
        inventory_status = (
            current_inventory.status if current_inventory else "sin_inventario"
        )

        response_text = f"""✅ **¡Producto Editado Exitosamente!**

**Producto:** {updated_product.name}
**SKU:** {updated_product.sku}

{changes_text}

**Estado actual del inventario:** {inventory_status}
**Cantidad actual:** {current_inventory.quantity if current_inventory else 0} unidades

¡La información del producto ha sido actualizada correctamente!"""

        return ChatResponse(
            response=response_text,
            data={
                "product_id": updated_product.id,
                "product_name": updated_product.name,
                "changes_made": len(changes),
                "current_stock": current_inventory.quantity if current_inventory else 0,
                "inventory_status": inventory_status,
                "old_values": old_values,
                "updated_values": {
                    "name": updated_product.name,
                    "price": float(updated_product.price),
                    "category": updated_product.category,
                    "description": updated_product.description or "",
                    "quantity": current_inventory.quantity if current_inventory else 0,
                    "min_threshold": (
                        current_inventory.min_threshold if current_inventory else 0
                    ),
                    "max_threshold": (
                        current_inventory.max_threshold if current_inventory else 0
                    ),
                },
            },
            workflow_id=f"edit-product-{updated_product.id}",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error editing product: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error editando producto: {str(e)}"
        )


@router.get("/products-with-stock")
async def get_products_with_stock(
    session: AsyncSession = Depends(get_async_session),
):
    """Get all products with their current stock information."""
    try:
        db_service = DatabaseService(session)
        products_with_stock = await db_service.get_products_with_stock()

        return {
            "products": products_with_stock,
            "total_products": len(products_with_stock),
            "total_units": sum(p["stock_quantity"] for p in products_with_stock),
            "low_stock_items": len(
                [
                    p
                    for p in products_with_stock
                    if p["stock_status"] in ["crítico", "agotado"]
                ]
            ),
        }
    except Exception as e:
        logger.error(f"Error getting products with stock: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error obteniendo productos: {str(e)}"
        )


@router.get("/summary")
async def get_inventory_summary(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Get inventory summary statistics."""
    try:
        db_service = DatabaseService(session)
        summary = await db_service.get_inventory_summary()

        return summary
    except Exception as e:
        logger.error(f"Error getting inventory summary: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error obteniendo resumen: {str(e)}"
        )


@router.delete("/product/{product_id}")
async def delete_product(
    product_id: int,
    session: AsyncSession = Depends(get_async_session),
):
    """Delete a product and its inventory items."""
    try:
        db_service = DatabaseService(session)

        # Check if product exists
        product = await db_service.get_product_by_id(product_id)
        if not product:
            raise HTTPException(
                status_code=404, detail=f"Producto con ID {product_id} no encontrado"
            )

        product_name = product.name

        # Delete the product (will cascade to inventory items)
        success = await db_service.delete_product(product_id)
        if not success:
            raise HTTPException(status_code=500, detail="Error eliminando el producto")

        return {
            "message": f"Producto '{product_name}' eliminado exitosamente",
            "product_id": product_id,
            "product_name": product_name,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting product: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error eliminando producto: {str(e)}"
        )


@router.get("/debug/data")
async def debug_inventory_data(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Debug endpoint to view all inventory data."""
    try:
        db_service = DatabaseService(session)

        products = await db_service.get_all_products()
        products_with_stock = await db_service.get_products_with_stock()
        summary = await db_service.get_inventory_summary()

        return {
            "database_info": {
                "total_products": len(products),
                "products_with_inventory": len(products_with_stock),
                "summary": summary,
            },
            "products": [db_service._product_to_dict(p) for p in products],
            "products_with_stock": products_with_stock,
        }
    except Exception as e:
        logger.error(f"Error in debug endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error en debug: {str(e)}")
