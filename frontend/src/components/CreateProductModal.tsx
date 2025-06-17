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
  Electrónicos: 'Electrónicos',
  Muebles: 'Muebles',
  Electrodomésticos: 'Electrodomésticos',
  Ropa: 'Ropa',
  Libros: 'Libros',
  Deportes: 'Deportes',
  Automóviles: 'Automóviles',
  Alimentos: 'Alimentos',
  Otros: 'Otros',
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
      if (!product.price || product.price <= 0) {
        errors.push(
          `Producto ${index + 1}: El precio es obligatorio y debe ser mayor a 0`
        );
      }
      if (!product.category || !product.category.trim()) {
        errors.push(`Producto ${index + 1}: La categoría es obligatoria`);
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
            price: product.price!, // Now required, so we can use non-null assertion
            category:
              CATEGORIES[product.category! as keyof typeof CATEGORIES] ||
              'Other',
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
    return (
      product.name.trim() &&
      product.quantity >= 1 &&
      product.price !== undefined &&
      product.price > 0 &&
      product.category &&
      product.category.trim()
    );
  };

  const canSubmit = products.some(isProductValid) && !submitting;

  return (
    <div className='fixed inset-0 backdrop-blur-sm bg-black/30 flex items-center justify-center z-50 p-4'>
      <div className='relative backdrop-blur-xl bg-slate-900/90 border border-white/20 rounded-2xl shadow-2xl max-w-6xl w-full max-h-[90vh] overflow-hidden'>
        <div className='absolute inset-0 rounded-2xl bg-gradient-to-br from-slate-800/50 via-purple-900/30 to-slate-800/50 pointer-events-none' />

        {/* Header */}
        <div className='relative z-10 flex items-center justify-between p-6 border-b border-white/10'>
          <div className='flex items-center space-x-3'>
            <Package className='h-6 w-6 text-green-400' />
            <h2 className='text-xl font-semibold text-white'>
              Agregar Productos al Inventario
            </h2>
          </div>
          <button
            onClick={handleClose}
            className='text-white/70 hover:text-white transition-colors p-2 hover:bg-white/10 rounded-lg'
            disabled={submitting}
          >
            <X className='h-6 w-6' />
          </button>
        </div>

        {/* Content */}
        <div className='relative z-10 p-6 max-h-[60vh] overflow-y-auto'>
          {error && (
            <div className='mb-4 p-3 bg-red-500/20 border border-red-500/30 rounded-lg flex items-start space-x-2'>
              <AlertCircle className='h-5 w-5 text-red-400 mt-0.5 flex-shrink-0' />
              <span className='text-sm text-red-300'>{error}</span>
            </div>
          )}

          <div className='space-y-4'>
            {products.map((product, index) => (
              <div
                key={product.id}
                className={`p-4 border rounded-lg ${
                  successProducts.includes(product.name)
                    ? 'border-green-400/30 bg-green-500/10'
                    : 'border-white/20 bg-white/5'
                }`}
              >
                <div className='flex items-center justify-between mb-3'>
                  <h3 className='font-medium text-white flex items-center space-x-2'>
                    <span>Producto {index + 1}</span>
                    {successProducts.includes(product.name) && (
                      <Check className='h-4 w-4 text-green-400' />
                    )}
                  </h3>
                  {products.length > 1 && (
                    <button
                      onClick={() => removeProduct(product.id)}
                      className='text-red-400 hover:text-red-300 transition-colors'
                      disabled={submitting}
                    >
                      <Trash2 className='h-4 w-4' />
                    </button>
                  )}
                </div>

                <div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
                  {/* Product Name - Required */}
                  <div>
                    <label className='block text-sm font-medium text-white/80 mb-1'>
                      Nombre del Producto *
                    </label>
                    <input
                      type='text'
                      value={product.name}
                      onChange={(e) =>
                        updateProduct(product.id, 'name', e.target.value)
                      }
                      className='w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:ring-2 focus:ring-green-400 focus:border-green-400'
                      placeholder='Ej: Laptop HP Pavilion'
                      disabled={submitting}
                    />
                  </div>

                  {/* Quantity - Required */}
                  <div>
                    <label className='block text-sm font-medium text-white/80 mb-1'>
                      Cantidad *
                    </label>
                    <div className='flex items-center space-x-2'>
                      <button
                        onClick={() => updateQuantity(product.id, -1)}
                        className='p-1 text-white/60 hover:text-white bg-white/10 border border-white/20 rounded'
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
                        className='w-20 px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-center text-white focus:ring-2 focus:ring-green-400 focus:border-green-400'
                        min='1'
                        disabled={submitting}
                      />
                      <button
                        onClick={() => updateQuantity(product.id, 1)}
                        className='p-1 text-white/60 hover:text-white bg-white/10 border border-white/20 rounded'
                        disabled={submitting}
                      >
                        <Plus className='h-4 w-4' />
                      </button>
                    </div>
                  </div>

                  {/* Category - Required */}
                  <div>
                    <label className='block text-sm font-medium text-white/80 mb-1'>
                      Categoría *
                    </label>
                    <select
                      value={product.category || ''}
                      onChange={(e) =>
                        updateProduct(product.id, 'category', e.target.value)
                      }
                      className='w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:ring-2 focus:ring-green-400 focus:border-green-400'
                      disabled={submitting}
                    >
                      <option value='' className='bg-slate-800 text-white'>
                        Seleccionar categoría
                      </option>
                      {Object.keys(CATEGORIES).map((cat) => (
                        <option
                          key={cat}
                          value={cat}
                          className='bg-slate-800 text-white'
                        >
                          {cat}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Price - Required */}
                  <div>
                    <label className='block text-sm font-medium text-white/80 mb-1'>
                      Precio *
                    </label>
                    <div className='relative'>
                      <span className='absolute left-3 top-2 text-white/60'>
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
                        className='w-full pl-8 pr-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:ring-2 focus:ring-green-400 focus:border-green-400'
                        placeholder='50.00'
                        min='0'
                        step='0.01'
                        disabled={submitting}
                      />
                    </div>
                  </div>

                  {/* Description - Optional */}
                  <div className='md:col-span-2'>
                    <label className='block text-sm font-medium text-white/80 mb-1'>
                      Descripción
                    </label>
                    <textarea
                      value={product.description || ''}
                      onChange={(e) =>
                        updateProduct(product.id, 'description', e.target.value)
                      }
                      className='w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:ring-2 focus:ring-green-400 focus:border-green-400'
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
              className='flex items-center space-x-2 px-4 py-2 bg-white/10 border border-white/20 text-white/80 rounded-lg hover:bg-white/20 hover:text-white transition-colors'
              disabled={submitting}
            >
              <Plus className='h-4 w-4' />
              <span>Agregar otro producto</span>
            </button>
          </div>
        </div>

        {/* Footer */}
        <div className='relative z-10 flex items-center justify-between p-6 border-t border-white/10 bg-white/5'>
          <div className='text-sm text-white/60'>
            * Campos obligatorios: Nombre, Precio, Cantidad y Categoría
          </div>
          <div className='flex space-x-3'>
            <button
              onClick={handleClose}
              className='px-4 py-2 bg-white/10 border border-white/20 text-white/80 rounded-lg hover:bg-white/20 hover:text-white transition-colors'
              disabled={submitting}
            >
              Cancelar
            </button>
            <div className='w-full bg-white/5 rounded-xl'>
              <button
                onClick={handleSubmit}
                disabled={!canSubmit}
                className={`w-full py-3 px-4 rounded-xl font-medium transition-all duration-300 shadow-lg ${
                  canSubmit
                    ? 'bg-gradient-to-r from-green-500 to-emerald-600 text-white hover:from-green-600 hover:to-emerald-700'
                    : 'bg-gray-500 text-white/40 cursor-not-allowed'
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
    </div>
  );
};

export default CreateProductModal;
