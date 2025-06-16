/* eslint-disable @typescript-eslint/no-explicit-any */
'use client';

import React, { useState } from 'react';
import {
  X,
  Plus,
  Minus,
  Package,
  AlertCircle,
  Check,
  Trash2,
} from 'lucide-react';
import Cookies from 'js-cookie';

interface ProductToAdd {
  id: string;
  name: string;
  quantity: number;
  category?: string;
  price?: number;
  description?: string;
}

interface CreateProductModalProps {
  isOpen: boolean;
  onClose: () => void;
  onProductsCreated: (message: string) => void;
}

const CATEGORIES = {
  Electrónicos: 'Electronics',
  Muebles: 'Furniture',
  Electrodomésticos: 'Appliances',
  Ropa: 'Clothing',
  Libros: 'Books',
  Deportes: 'Sports',
  Automóviles: 'Automotive',
  Alimentos: 'Food',
  Otros: 'Other',
};

const CreateProductModal: React.FC<CreateProductModalProps> = ({
  isOpen,
  onClose,
  onProductsCreated,
}) => {
  const [products, setProducts] = useState<ProductToAdd[]>([
    { id: '1', name: '', quantity: 1 },
  ]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successProducts, setSuccessProducts] = useState<string[]>([]);

  if (!isOpen) return null;

  const addNewProduct = () => {
    const newId = (Date.now() + Math.random()).toString();
    setProducts([...products, { id: newId, name: '', quantity: 1 }]);
  };

  const removeProduct = (id: string) => {
    if (products.length > 1) {
      setProducts(products.filter((p) => p.id !== id));
    }
  };

  const updateProduct = (id: string, field: keyof ProductToAdd, value: any) => {
    setProducts(
      products.map((p) => (p.id === id ? { ...p, [field]: value } : p))
    );
    setError(null);
  };

  const updateQuantity = (id: string, delta: number) => {
    setProducts(
      products.map((p) =>
        p.id === id ? { ...p, quantity: Math.max(1, p.quantity + delta) } : p
      )
    );
  };

  const validateProducts = () => {
    const errors: string[] = [];

    products.forEach((product, index) => {
      if (!product.name.trim()) {
        errors.push(`Producto ${index + 1}: El nombre es obligatorio`);
      }
      if (product.quantity < 1) {
        errors.push(`Producto ${index + 1}: La cantidad debe ser mayor a 0`);
      }
      if (product.price !== undefined && product.price < 0) {
        errors.push(`Producto ${index + 1}: El precio no puede ser negativo`);
      }
    });

    return errors;
  };

  const handleSubmit = async () => {
    const validationErrors = validateProducts();
    if (validationErrors.length > 0) {
      setError(validationErrors.join(', '));
      return;
    }

    setSubmitting(true);
    setError(null);
    setSuccessProducts([]);

    try {
      const token = Cookies.get('auth_token');
      const API_BASE_URL =
        process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

      const results = [];
      const failures = [];

      // Submit each product individually
      for (const product of products) {
        try {
          const productData = {
            name: product.name.trim(),
            quantity: product.quantity,
            price: product.price || 50.0, // Default price if not provided
            category: product.category
              ? CATEGORIES[product.category as keyof typeof CATEGORIES] ||
                'Other'
              : 'Other',
            description: product.description || '',
          };

          const response = await fetch(
            `${API_BASE_URL}/inventory/add-product`,
            {
              method: 'POST',
              headers: {
                Authorization: `Bearer ${token}`,
                'Content-Type': 'application/json',
              },
              body: JSON.stringify(productData),
            }
          );

          if (!response.ok) {
            const errorData = await response.json();
            throw new Error(
              errorData.detail || `Error agregando producto ${product.name}`
            );
          }

          const result = await response.json();
          results.push({ product: product.name, result });
          setSuccessProducts((prev) => [...prev, product.name]);
        } catch (err) {
          const errorMessage =
            err instanceof Error ? err.message : 'Error desconocido';
          failures.push(`${product.name}: ${errorMessage}`);
        }
      }

      // Generate success message
      let message = '';
      if (results.length > 0) {
        message += `✅ **${results.length} producto(s) agregado(s) exitosamente:**\n\n`;
        results.forEach(({ product }) => {
          message += `• ${product}\n`;
        });
      }

      if (failures.length > 0) {
        message += `\n❌ **${failures.length} producto(s) fallaron:**\n\n`;
        failures.forEach((failure) => {
          message += `• ${failure}\n`;
        });
      }

      // If all succeeded, close modal and reset
      if (failures.length === 0) {
        onProductsCreated(message);
        handleClose();
      } else {
        // Show partial success
        onProductsCreated(message);
        setError(`${failures.length} de ${products.length} productos fallaron`);
      }
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Error procesando productos';
      setError(errorMessage);
    } finally {
      setSubmitting(false);
    }
  };

  const handleClose = () => {
    setProducts([{ id: '1', name: '', quantity: 1 }]);
    setError(null);
    setSuccessProducts([]);
    onClose();
  };

  const isProductValid = (product: ProductToAdd) => {
    return product.name.trim() && product.quantity >= 1;
  };

  const canSubmit = products.some(isProductValid) && !submitting;

  return (
    <div className='fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4'>
      <div className='bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-hidden'>
        {/* Header */}
        <div className='flex items-center justify-between p-6 border-b border-gray-200'>
          <div className='flex items-center space-x-3'>
            <Package className='h-6 w-6 text-green-600' />
            <h2 className='text-xl font-semibold text-gray-900'>
              Agregar Productos al Inventario
            </h2>
          </div>
          <button
            onClick={handleClose}
            className='text-gray-400 hover:text-gray-600 transition-colors'
            disabled={submitting}
          >
            <X className='h-6 w-6' />
          </button>
        </div>

        {/* Content */}
        <div className='p-6 max-h-[60vh] overflow-y-auto'>
          {error && (
            <div className='mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-start space-x-2'>
              <AlertCircle className='h-5 w-5 text-red-500 mt-0.5 flex-shrink-0' />
              <span className='text-sm text-red-700'>{error}</span>
            </div>
          )}

          <div className='space-y-4'>
            {products.map((product, index) => (
              <div
                key={product.id}
                className={`p-4 border rounded-lg ${
                  successProducts.includes(product.name)
                    ? 'border-green-200 bg-green-50'
                    : 'border-gray-200'
                }`}
              >
                <div className='flex items-center justify-between mb-3'>
                  <h3 className='font-medium text-gray-900 flex items-center space-x-2'>
                    <span>Producto {index + 1}</span>
                    {successProducts.includes(product.name) && (
                      <Check className='h-4 w-4 text-green-500' />
                    )}
                  </h3>
                  {products.length > 1 && (
                    <button
                      onClick={() => removeProduct(product.id)}
                      className='text-red-500 hover:text-red-700 transition-colors'
                      disabled={submitting}
                    >
                      <Trash2 className='h-4 w-4' />
                    </button>
                  )}
                </div>

                <div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
                  {/* Product Name - Required */}
                  <div>
                    <label className='block text-sm font-medium text-gray-700 mb-1'>
                      Nombre del Producto *
                    </label>
                    <input
                      type='text'
                      value={product.name}
                      onChange={(e) =>
                        updateProduct(product.id, 'name', e.target.value)
                      }
                      className='w-full px-3 py-2 border border-gray-300 rounded-lg text-gray-900 focus:ring-2 focus:ring-green-500 focus:border-green-500'
                      placeholder='Ej: Laptop HP Pavilion'
                      disabled={submitting}
                    />
                  </div>

                  {/* Quantity - Required */}
                  <div>
                    <label className='block text-sm font-medium text-gray-700 mb-1'>
                      Cantidad *
                    </label>
                    <div className='flex items-center space-x-2'>
                      <button
                        onClick={() => updateQuantity(product.id, -1)}
                        className='p-1 text-gray-500 hover:text-gray-700 border border-gray-300 rounded'
                        disabled={product.quantity <= 1 || submitting}
                      >
                        <Minus className='h-4 w-4' />
                      </button>
                      <input
                        type='number'
                        value={product.quantity}
                        onChange={(e) =>
                          updateProduct(
                            product.id,
                            'quantity',
                            Math.max(1, parseInt(e.target.value) || 1)
                          )
                        }
                        className='w-20 px-3 py-2 border border-gray-300 rounded-lg text-center text-gray-900 focus:ring-2 focus:ring-green-500 focus:border-green-500'
                        min='1'
                        disabled={submitting}
                      />
                      <button
                        onClick={() => updateQuantity(product.id, 1)}
                        className='p-1 text-gray-500 hover:text-gray-700 border border-gray-300 rounded'
                        disabled={submitting}
                      >
                        <Plus className='h-4 w-4' />
                      </button>
                    </div>
                  </div>

                  {/* Category - Optional */}
                  <div>
                    <label className='block text-sm font-medium text-gray-700 mb-1'>
                      Categoría
                    </label>
                    <select
                      value={product.category || ''}
                      onChange={(e) =>
                        updateProduct(product.id, 'category', e.target.value)
                      }
                      className='w-full px-3 py-2 border border-gray-300 rounded-lg text-gray-900 focus:ring-2 focus:ring-green-500 focus:border-green-500'
                      disabled={submitting}
                    >
                      <option value=''>Seleccionar categoría</option>
                      {Object.keys(CATEGORIES).map((cat) => (
                        <option key={cat} value={cat}>
                          {cat}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Price - Optional */}
                  <div>
                    <label className='block text-sm font-medium text-gray-700 mb-1'>
                      Precio
                    </label>
                    <div className='relative'>
                      <span className='absolute left-3 top-2 text-gray-500'>
                        $
                      </span>
                      <input
                        type='number'
                        value={product.price || ''}
                        onChange={(e) =>
                          updateProduct(
                            product.id,
                            'price',
                            e.target.value
                              ? parseFloat(e.target.value)
                              : undefined
                          )
                        }
                        className='w-full pl-8 pr-3 py-2 border border-gray-300 rounded-lg text-gray-900 focus:ring-2 focus:ring-green-500 focus:border-green-500'
                        placeholder='50.00'
                        min='0'
                        step='0.01'
                        disabled={submitting}
                      />
                    </div>
                  </div>

                  {/* Description - Optional */}
                  <div className='md:col-span-2'>
                    <label className='block text-sm font-medium text-gray-700 mb-1'>
                      Descripción
                    </label>
                    <textarea
                      value={product.description || ''}
                      onChange={(e) =>
                        updateProduct(product.id, 'description', e.target.value)
                      }
                      className='w-full px-3 py-2 border border-gray-300 rounded-lg text-gray-900 focus:ring-2 focus:ring-green-500 focus:border-green-500'
                      placeholder='Descripción opcional del producto'
                      rows={2}
                      disabled={submitting}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Add Product Button */}
          <div className='mt-4 flex justify-center'>
            <button
              onClick={addNewProduct}
              className='flex items-center space-x-2 px-4 py-2 border border-green-300 text-green-700 rounded-lg hover:bg-green-50 transition-colors'
              disabled={submitting}
            >
              <Plus className='h-4 w-4' />
              <span>Agregar otro producto</span>
            </button>
          </div>
        </div>

        {/* Footer */}
        <div className='flex items-center justify-between p-6 border-t border-gray-200 bg-gray-50'>
          <div className='text-sm text-gray-600'>
            * Campos obligatorios: Nombre y Cantidad
          </div>
          <div className='flex space-x-3'>
            <button
              onClick={handleClose}
              className='px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors'
              disabled={submitting}
            >
              Cancelar
            </button>
            <button
              onClick={handleSubmit}
              disabled={!canSubmit}
              className={`px-6 py-2 rounded-lg font-medium transition-colors flex items-center space-x-2 ${
                canSubmit
                  ? 'bg-green-600 text-white hover:bg-green-700'
                  : 'bg-gray-300 text-gray-500 cursor-not-allowed'
              }`}
            >
              {submitting && (
                <div className='animate-spin rounded-full h-4 w-4 border-b-2 border-white'></div>
              )}
              <span>
                {submitting
                  ? 'Agregando...'
                  : `Agregar ${
                      products.filter(isProductValid).length
                    } producto(s)`}
              </span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CreateProductModal;
