"""
Product Agent for handling product CRUD operations and product management.
"""

import logging
import re
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from models.api_models import ChatResponse, ProductCreateRequest, ProductEditRequest
from services.database_service import DatabaseService


logger = logging.getLogger(__name__)


class ProductAgent:
    """Agent for handling product-related operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.db_service = DatabaseService(session)
        self.category_mapping = {
            "electrónicos": "Electronics",
            "electrodomésticos": "Appliances",
            "muebles": "Furniture",
            "ropa": "Clothing",
            "deportes": "Sports",
            "libros": "Books",
            "comida": "Food",
            "hogar": "Home",
            "juguetes": "Toys",
            "salud": "Health",
            "automotriz": "Automotive",
            "jardín": "Garden",
        }

    async def handle_add_product(self, message: str) -> ChatResponse:
        """Handle add product command with natural language parsing."""
        try:
            logger.info(f"📦 ADD_PRODUCT: Processing message: {message}")

            # Parse product data from natural language
            product_data = self._parse_product_data(message)

            if not product_data:
                return ChatResponse(
                    response="❌ No pude extraer la información del producto. "
                    "Puedes usar comandos como:\n"
                    "• 'Añadir producto Laptop con precio $800 y cantidad 10'\n"
                    "• 'Agregar Televisor, precio: $500, stock: 5, categoría: electrónicos'\n"
                    "• 'Nuevo producto: Silla, $150, 20 unidades'",
                    workflow_id="add-product-error-"
                    + datetime.now().strftime("%Y%m%d-%H%M%S"),
                )

            # Validate required fields
            if not product_data.get("name"):
                return ChatResponse(
                    response="❌ **Falta el nombre del producto**. "
                    "Especifica el nombre del producto que quieres añadir.",
                    workflow_id="add-product-name-error-"
                    + datetime.now().strftime("%Y%m%d-%H%M%S"),
                )

            if not product_data.get("price"):
                return ChatResponse(
                    response="❌ **Falta el precio del producto**. "
                    "Especifica el precio con formato como '$100' o 'precio 100'.",
                    workflow_id="add-product-price-error-"
                    + datetime.now().strftime("%Y%m%d-%H%M%S"),
                )

            if not product_data.get("quantity"):
                return ChatResponse(
                    response="❌ **Falta la cantidad del producto**. "
                    "Especifica la cantidad como 'cantidad 20' o '20 unidades'.",
                    workflow_id="add-product-quantity-error-"
                    + datetime.now().strftime("%Y%m%d-%H%M%S"),
                )

            # Set defaults for optional fields
            product_data.setdefault("category", "Other")
            product_data.setdefault("description", f"Producto {product_data['name']}")

            # Create product request
            create_request = ProductCreateRequest(
                name=product_data["name"],
                price=product_data["price"],
                category=product_data["category"],
                description=product_data["description"],
                quantity=product_data["quantity"],
            )

            # Create product
            product = await self.db_service.create_product(create_request)

            # Build success response
            response_text = f"""✅ **¡Producto Creado Exitosamente!** 🎉

**📦 Detalles del Producto:**
- **Nombre:** {product.name}
- **Precio:** ${product.price:.2f}
- **Categoría:** {product.category}
- **Descripción:** {product.description}
- **Stock inicial:** {product_data['quantity']} unidades
- **ID del producto:** #{product.id}

El producto ha sido añadido al inventario y está listo para la venta."""

            return ChatResponse(
                response=response_text,
                data={
                    "product_id": product.id,
                    "name": product.name,
                    "price": float(product.price),
                    "category": product.category,
                    "initial_stock": product_data["quantity"],
                },
                workflow_id=f"add-product-{product.id}",
            )

        except Exception as e:
            logger.error(f"Error in handle_add_product: {str(e)}")
            return ChatResponse(
                response=f"❌ Error añadiendo producto: {str(e)}",
                workflow_id="add-product-error-"
                + datetime.now().strftime("%Y%m%d-%H%M%S"),
            )

    async def handle_edit_inventory(self, message: str) -> ChatResponse:
        """Handle edit inventory command with natural language parsing."""
        try:
            logger.info(f"✏️ EDIT_INVENTORY: Processing message: {message}")

            # Parse edit data from natural language
            edit_data = self._parse_edit_data(message)

            if not edit_data:
                return ChatResponse(
                    response="❌ No pude extraer la información de edición. "
                    "Puedes usar comandos como:\n"
                    "• 'Editar producto ID 1, cambiar precio a $900'\n"
                    "• 'Actualizar Laptop precio $1000 cantidad 15'\n"
                    "• 'Modificar producto nombre: Laptop Gaming, precio: $1200'",
                    workflow_id="edit-inventory-error-"
                    + datetime.now().strftime("%Y%m%d-%H%M%S"),
                )

            # Find product by ID or name
            product = None
            if edit_data.get("product_id"):
                product = await self.db_service.get_product_by_id(
                    edit_data["product_id"]
                )
            elif edit_data.get("product_name"):
                # Search by name
                all_products = await self.db_service.get_all_products()
                search_name = edit_data["product_name"].lower()

                for p in all_products:
                    if search_name in p.name.lower() or p.name.lower() in search_name:
                        product = p
                        break

            if not product:
                return ChatResponse(
                    response="❌ **Producto no encontrado**. "
                    "Verifica el ID del producto o usa el nombre exacto. "
                    "Puedes listar productos con 'ver inventario'.",
                    workflow_id="edit-inventory-not-found-"
                    + datetime.now().strftime("%Y%m%d-%H%M%S"),
                )

            # Prepare edit request
            edit_request_data = {}

            # Update fields if provided
            if edit_data.get("name"):
                edit_request_data["name"] = edit_data["name"]
            if edit_data.get("price"):
                edit_request_data["price"] = edit_data["price"]
            if edit_data.get("category"):
                edit_request_data["category"] = edit_data["category"]
            if edit_data.get("description"):
                edit_request_data["description"] = edit_data["description"]

            if not edit_request_data:
                return ChatResponse(
                    response="❌ **No se especificaron cambios**. "
                    "Indica qué quieres modificar (precio, nombre, categoría, etc.)",
                    workflow_id="edit-inventory-no-changes-"
                    + datetime.now().strftime("%Y%m%d-%H%M%S"),
                )

            # Create edit request
            edit_request = ProductEditRequest(**edit_request_data)

            # Update product
            updated_product = await self.db_service.update_product(
                product.id, edit_request
            )

            # Handle quantity update separately if provided
            quantity_info = ""
            if edit_data.get("quantity"):
                # Update inventory quantity
                if updated_product.inventory_items:
                    inventory_item = updated_product.inventory_items[0]
                    await self.db_service.update_inventory_quantity(
                        inventory_item.id, edit_data["quantity"]
                    )
                    quantity_info = (
                        f"\n- **Nueva cantidad:** {edit_data['quantity']} unidades"
                    )

            # Build success response
            changes_made = []
            if edit_data.get("name"):
                changes_made.append(f"Nombre: {updated_product.name}")
            if edit_data.get("price"):
                changes_made.append(f"Precio: ${updated_product.price:.2f}")
            if edit_data.get("category"):
                changes_made.append(f"Categoría: {updated_product.category}")
            if edit_data.get("description"):
                changes_made.append(f"Descripción: {updated_product.description}")

            response_text = f"""✅ **¡Producto Actualizado Exitosamente!** ✏️

**📦 Producto:** {updated_product.name} (ID #{updated_product.id})

**🔄 Cambios realizados:**
{chr(10).join(f'- **{change}**' for change in changes_made)}{quantity_info}

**📊 Estado actual del producto:**
- **Precio:** ${updated_product.price:.2f}
- **Categoría:** {updated_product.category}
- **Descripción:** {updated_product.description}

¡El producto ha sido actualizado en el sistema!"""

            return ChatResponse(
                response=response_text,
                data={
                    "product_id": updated_product.id,
                    "name": updated_product.name,
                    "price": float(updated_product.price),
                    "category": updated_product.category,
                    "changes_made": changes_made,
                },
                workflow_id=f"edit-inventory-{updated_product.id}",
            )

        except Exception as e:
            logger.error(f"Error in handle_edit_inventory: {str(e)}")
            return ChatResponse(
                response=f"❌ Error editando producto: {str(e)}",
                workflow_id="edit-inventory-error-"
                + datetime.now().strftime("%Y%m%d-%H%M%S"),
            )

    def _parse_product_data(self, message: str) -> Optional[Dict[str, Any]]:
        """Parse product data from natural language message with flexible patterns."""
        product_data = {}

        # Extract name with multiple flexible patterns
        name_patterns = [
            # Traditional patterns
            r'(?:producto[:\s]+|nombre[:\s]+)["\']([^"\']+)["\']',  # "producto: 'Lija'"
            r"(?:producto[:\s]+|nombre[:\s]+)([^,\n]+)",  # "producto: Lija"
            # Natural language patterns
            r"(?:añade|añadir|agregar|crear)\s+(?:el\s+)?producto\s+([^,\s]+)",  # "Añade el producto Lija"
            r"(?:añade|añadir|agregar|crear)\s+([^,\s]+)\s+con",  # "Añade Lija con"
            r"producto\s+([^,\s]+)\s+(?:con|precio|valor)",  # "producto Lija con"
            r"nuevo\s+producto[:\s]*([^,\n]+)",  # "nuevo producto: Lija"
        ]

        for pattern in name_patterns:
            name_match = re.search(pattern, message, re.IGNORECASE)
            if name_match:
                product_name = name_match.group(1).strip()
                # Clean up common words
                product_name = re.sub(
                    r"\s+(con|y|de|precio|valor|cantidad).*$",
                    "",
                    product_name,
                    flags=re.IGNORECASE,
                )
                if product_name:
                    product_data["name"] = product_name
                    break

        # Extract price with multiple patterns
        price_patterns = [
            r"precio[:\s]*\$?(\d+(?:\.\d{2})?)",  # "precio $500"
            r"valor[:\s]*(?:de[:\s]*)?\$?(\d+(?:\.\d{2})?)",  # "valor de 500"
            r"cuesta[:\s]*\$?(\d+(?:\.\d{2})?)",  # "cuesta $500"
            r"con\s+(?:valor|precio)\s+(?:de\s+)?\$?(\d+(?:\.\d{2})?)",  # "con valor de 500"
            r"\$(\d+(?:\.\d{2})?)",  # "$500"
        ]

        for pattern in price_patterns:
            price_match = re.search(pattern, message, re.IGNORECASE)
            if price_match:
                product_data["price"] = float(price_match.group(1))
                break

        # Extract quantity with multiple patterns
        quantity_patterns = [
            r"cantidad[:\s]*(\d+)",  # "cantidad 20"
            r"(\d+)\s+unidades?",  # "20 unidades"
            r"y\s+(\d+)\s+unidades?",  # "y 20 unidades"
            r"con\s+(\d+)\s+unidades?",  # "con 20 unidades"
            r"stock[:\s]*(\d+)",  # "stock 20"
            r"inventario[:\s]*(\d+)",  # "inventario 20"
        ]

        for pattern in quantity_patterns:
            quantity_match = re.search(pattern, message, re.IGNORECASE)
            if quantity_match:
                product_data["quantity"] = int(quantity_match.group(1))
                break

        # Extract category (map Spanish to English)
        category_patterns = [
            r"categoría[:\s]*([^,\n]+)",  # "categoría electrónicos"
            r"tipo[:\s]*([^,\n]+)",  # "tipo electrónicos"
            r"es\s+(?:un|una)\s+([^,\n]+)",  # "es un electrónico"
        ]

        for pattern in category_patterns:
            category_match = re.search(pattern, message, re.IGNORECASE)
            if category_match:
                category_spanish = category_match.group(1).strip().lower()
                product_data["category"] = self.category_mapping.get(
                    category_spanish, category_spanish.title()
                )
                break

        # Extract description
        desc_patterns = [
            r"descripción[:\s]*([^,\n]+)",  # "descripción: ..."
            r"describe[:\s]*([^,\n]+)",  # "describe: ..."
        ]

        for pattern in desc_patterns:
            desc_match = re.search(pattern, message, re.IGNORECASE)
            if desc_match:
                product_data["description"] = desc_match.group(1).strip()
                break

        return product_data if product_data.get("name") else None

    def _parse_edit_data(self, message: str) -> Optional[Dict[str, Any]]:
        """Parse edit data from natural language message with flexible patterns."""
        edit_data = {}

        # Extract product ID (traditional method)
        id_match = re.search(r"(?:producto|id)[:\s]*(\d+)", message, re.IGNORECASE)
        if id_match:
            edit_data["product_id"] = int(id_match.group(1))

        # Extract product name for search (more flexible patterns)
        product_name = None

        # Pattern 1: "Actualizar [PRODUCT_NAME] a/precio..."
        update_match = re.search(
            r"actualizar\s+([^a-z]+?)(?:\s+a\s+|\s+precio\s+)", message, re.IGNORECASE
        )
        if update_match:
            product_name = update_match.group(1).strip()

        # Pattern 2: "Editar [PRODUCT_NAME] cambiar..." or "Editar producto [PRODUCT_NAME], ..."
        edit_patterns = [
            r"editar\s+producto\s+([^,]+?)(?:\s*,|\s+cambiar|\s+precio|\s+cantidad)",  # "Editar producto [NAME], ..."
            r"editar\s+([^,]+?)(?:\s*,|\s+cambiar|\s+precio|\s+cantidad)",  # "Editar [NAME], ..."
        ]

        for pattern in edit_patterns:
            edit_match = re.search(pattern, message, re.IGNORECASE)
            if edit_match:
                potential_name = edit_match.group(1).strip()
                # Skip if it's just "producto" or starts with "id"
                if (
                    not potential_name.lower().startswith("id")
                    and potential_name.lower() != "producto"
                ):
                    product_name = potential_name
                    break

        # Pattern 3: Traditional "nombre: [NAME]"
        name_match = re.search(
            r'nombre[:\s]*["\']([^"\']+)["\']|nombre[:\s]*([^,\n]+)',
            message,
            re.IGNORECASE,
        )
        if name_match:
            edit_data["name"] = (name_match.group(1) or name_match.group(2)).strip()

        # If we found a product name from patterns, store it for search
        if product_name and not edit_data.get("name"):
            edit_data["product_name"] = product_name

        # Extract price
        price_patterns = [
            r"precio[:\s]*(?:a[:\s]*)?\$?(\d+(?:\.\d{2})?)",  # "precio a $500"
            r"cambiar\s+precio\s+a\s+\$?(\d+(?:\.\d{2})?)",  # "cambiar precio a 500"
            r"\$(\d+(?:\.\d{2})?)",  # "$500"
        ]

        for pattern in price_patterns:
            price_match = re.search(pattern, message, re.IGNORECASE)
            if price_match:
                edit_data["price"] = float(price_match.group(1))
                break

        # Extract quantity
        quantity_patterns = [
            r"cantidad[:\s]*(?:a[:\s]*)?(\d+)",  # "cantidad a 20"
            r"cambiar\s+cantidad\s+a\s+(\d+)",  # "cambiar cantidad a 20"
            r"(\d+)\s+unidades?",  # "20 unidades"
            r"stock[:\s]*(\d+)",  # "stock 20"
        ]

        for pattern in quantity_patterns:
            quantity_match = re.search(pattern, message, re.IGNORECASE)
            if quantity_match:
                edit_data["quantity"] = int(quantity_match.group(1))
                break

        # Extract category
        category_patterns = [
            r"categoría[:\s]*(?:a[:\s]*)?([^,\n]+)",  # "categoría a electrónicos"
            r"cambiar\s+categoría\s+a\s+([^,\n]+)",  # "cambiar categoría a electrónicos"
        ]

        for pattern in category_patterns:
            category_match = re.search(pattern, message, re.IGNORECASE)
            if category_match:
                category_spanish = category_match.group(1).strip().lower()
                edit_data["category"] = self.category_mapping.get(
                    category_spanish, category_spanish.title()
                )
                break

        # Extract description
        desc_patterns = [
            r"descripción[:\s]*(?:a[:\s]*)?([^,\n]+)",  # "descripción a ..."
            r"cambiar\s+descripción\s+a\s+([^,\n]+)",  # "cambiar descripción a ..."
        ]

        for pattern in desc_patterns:
            desc_match = re.search(pattern, message, re.IGNORECASE)
            if desc_match:
                edit_data["description"] = desc_match.group(1).strip()
                break

        return edit_data if edit_data else None
