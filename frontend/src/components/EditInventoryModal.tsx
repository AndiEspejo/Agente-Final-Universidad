/* eslint-disable @typescript-eslint/no-explicit-any */
'use client';

import React, { useState, useEffect } from 'react';
import {
  X,
  Edit,
  Search,
  Package,
  AlertCircle,
  Check,
  Loader2,
} from 'lucide-react';
import Cookies from 'js-cookie';

interface Product {
  id: number;
  name: string;
  sku: string;
  price: number;
  category: string;
  stock_quantity: number;
  stock_status: string;
  location: string;
  available_for_sale: boolean;
}

interface EditInventoryModalProps {
  isOpen: boolean;
  onClose: () => void;
  onProductEdited: (message: string) => void;
}

const CATEGORIES = {
  Electronics: 'Electrónicos',
  Furniture: 'Muebles',
  Appliances: 'Electrodomésticos',
  Clothing: 'Ropa',
  Books: 'Libros',
  Sports: 'Deportes',
  Automotive: 'Automóviles',
  Food: 'Alimentos',
  Other: 'Otros',
};

const EditInventoryModal: React.FC<EditInventoryModalProps> = ({
  isOpen,
  onClose,
  onProductEdited,
}) => {
  const [products, setProducts] = useState<Product[]>([]);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form fields
  const [editForm, setEditForm] = useState({
    name: '',
    price: '',
    quantity: '',
    category: '',
    description: '',
    minimum_stock: '',
    maximum_stock: '',
  });

  useEffect(() => {
    if (isOpen) {
      loadProducts();
    }
  }, [isOpen]);

  useEffect(() => {
    if (selectedProduct) {
      setEditForm({
        name: selectedProduct.name,
        price: selectedProduct.price.toString(),
        quantity: selectedProduct.stock_quantity.toString(),
        category:
          CATEGORIES[selectedProduct.category as keyof typeof CATEGORIES] ||
          selectedProduct.category,
        description: '',
        minimum_stock: '',
        maximum_stock: '',
      });
    }
  }, [selectedProduct]);

  const loadProducts = async () => {
    setLoading(true);
    setError(null);

    try {
      const token = Cookies.get('auth_token');
      const API_BASE_URL =
        process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

      const response = await fetch(
        `${API_BASE_URL}/inventory/products-with-stock`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error('Error cargando productos');
      }

      const data = await response.json();
      setProducts(data.products || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error desconocido');
    } finally {
      setLoading(false);
    }
  };

  const filteredProducts = products.filter(
    (product) =>
      product.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      product.sku.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleSubmit = async () => {
    if (!selectedProduct) return;

    setSubmitting(true);
    setError(null);

    try {
      const token = Cookies.get('auth_token');
      const API_BASE_URL =
        process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

      // Build the edit request with only changed fields
      const editRequest: any = {
        product_id: selectedProduct.id,
      };

      if (editForm.name !== selectedProduct.name) {
        editRequest.name = editForm.name;
      }
      if (parseFloat(editForm.price) !== selectedProduct.price) {
        editRequest.price = parseFloat(editForm.price);
      }
      if (parseInt(editForm.quantity) !== selectedProduct.stock_quantity) {
        editRequest.quantity = parseInt(editForm.quantity);
      }

      const originalCategory =
        CATEGORIES[selectedProduct.category as keyof typeof CATEGORIES] ||
        selectedProduct.category;
      if (editForm.category !== originalCategory) {
        // Convert back to English for API
        const categoryKey = Object.keys(CATEGORIES).find(
          (key) =>
            CATEGORIES[key as keyof typeof CATEGORIES] === editForm.category
        );
        editRequest.category = categoryKey || editForm.category;
      }

      if (editForm.minimum_stock) {
        editRequest.minimum_stock = parseInt(editForm.minimum_stock);
      }
      if (editForm.maximum_stock) {
        editRequest.maximum_stock = parseInt(editForm.maximum_stock);
      }

      const response = await fetch(`${API_BASE_URL}/inventory/edit-product`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(editRequest),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Error editando producto');
      }

      const result = await response.json();
      onProductEdited(result.response);
      handleClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error desconocido');
    } finally {
      setSubmitting(false);
    }
  };

  const handleClose = () => {
    setSelectedProduct(null);
    setSearchTerm('');
    setEditForm({
      name: '',
      price: '',
      quantity: '',
      category: '',
      description: '',
      minimum_stock: '',
      maximum_stock: '',
    });
    setError(null);
    onClose();
  };

  const getStockStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'crítico':
        return 'text-red-600 bg-red-50';
      case 'bajo':
        return 'text-yellow-600 bg-yellow-50';
      case 'agotado':
        return 'text-gray-600 bg-gray-50';
      default:
        return 'text-green-600 bg-green-50';
    }
  };

  if (!isOpen) return null;

  return (
    <div className='fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4'>
      <div className='bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden'>
        {/* Header */}
        <div className='flex items-center justify-between p-6 border-b'>
          <h2 className='text-2xl font-bold text-gray-900 flex items-center gap-2'>
            <Edit className='w-6 h-6 text-purple-600' />
            Editar Inventario
          </h2>
          <button
            onClick={handleClose}
            className='text-gray-400 hover:text-gray-600 transition-colors'
          >
            <X className='w-6 h-6' />
          </button>
        </div>

        <div className='flex h-[600px]'>
          {/* Product List */}
          <div className='w-1/2 border-r'>
            <div className='p-4 border-b'>
              <div className='relative'>
                <Search className='absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4' />
                <input
                  type='text'
                  placeholder='Buscar productos...'
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className='w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500'
                />
              </div>
            </div>

            <div className='overflow-y-auto h-[500px] p-4'>
              {loading ? (
                <div className='flex items-center justify-center h-32'>
                  <Loader2 className='h-6 w-6 animate-spin text-gray-400' />
                  <span className='ml-2 text-gray-600'>
                    Cargando productos...
                  </span>
                </div>
              ) : filteredProducts.length === 0 ? (
                <div className='text-center text-gray-500 py-8'>
                  {searchTerm
                    ? 'No se encontraron productos'
                    : 'No hay productos disponibles'}
                </div>
              ) : (
                <div className='space-y-2'>
                  {filteredProducts.map((product) => (
                    <div
                      key={product.id}
                      onClick={() => setSelectedProduct(product)}
                      className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                        selectedProduct?.id === product.id
                          ? 'border-purple-500 bg-purple-50'
                          : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                      }`}
                    >
                      <div className='flex items-center justify-between'>
                        <div className='flex-1'>
                          <h3 className='font-medium text-gray-900'>
                            {product.name}
                          </h3>
                          <p className='text-sm text-gray-500'>
                            SKU: {product.sku}
                          </p>
                          <div className='flex items-center gap-2 mt-1'>
                            <span className='text-sm font-medium'>
                              ${product.price}
                            </span>
                            <span
                              className={`px-2 py-1 rounded-full text-xs ${getStockStatusColor(
                                product.stock_status
                              )}`}
                            >
                              {product.stock_quantity} unidades
                            </span>
                          </div>
                        </div>
                        <Package className='h-5 w-5 text-gray-400' />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Edit Form */}
          <div className='w-1/2 p-6 overflow-y-auto'>
            {selectedProduct ? (
              <div className='space-y-4'>
                <div className='text-lg font-medium text-gray-900 mb-4'>
                  Editando: {selectedProduct.name}
                </div>

                {error && (
                  <div className='bg-red-50 border border-red-200 rounded-lg p-3 flex items-center gap-2'>
                    <AlertCircle className='h-4 w-4 text-red-600 flex-shrink-0' />
                    <span className='text-red-700 text-sm'>{error}</span>
                  </div>
                )}

                <div>
                  <label className='block text-sm font-medium text-gray-700 mb-1'>
                    Nombre del Producto
                  </label>
                  <input
                    type='text'
                    value={editForm.name}
                    onChange={(e) =>
                      setEditForm({ ...editForm, name: e.target.value })
                    }
                    className='w-full border border-gray-300 rounded-lg px-3 py-2 bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500'
                  />
                </div>

                <div className='grid grid-cols-2 gap-4'>
                  <div>
                    <label className='block text-sm font-medium text-gray-700 mb-1'>
                      Precio ($)
                    </label>
                    <input
                      type='number'
                      step='0.01'
                      value={editForm.price}
                      onChange={(e) =>
                        setEditForm({ ...editForm, price: e.target.value })
                      }
                      className='w-full border border-gray-300 rounded-lg px-3 py-2 bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500'
                    />
                  </div>
                  <div>
                    <label className='block text-sm font-medium text-gray-700 mb-1'>
                      Cantidad
                    </label>
                    <input
                      type='number'
                      value={editForm.quantity}
                      onChange={(e) =>
                        setEditForm({ ...editForm, quantity: e.target.value })
                      }
                      className='w-full border border-gray-300 rounded-lg px-3 py-2 bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500'
                    />
                  </div>
                </div>

                <div>
                  <label className='block text-sm font-medium text-gray-700 mb-1'>
                    Categoría
                  </label>
                  <select
                    value={editForm.category}
                    onChange={(e) =>
                      setEditForm({ ...editForm, category: e.target.value })
                    }
                    className='w-full border border-gray-300 rounded-lg px-3 py-2 bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500'
                  >
                    {Object.values(CATEGORIES).map((category) => (
                      <option key={category} value={category}>
                        {category}
                      </option>
                    ))}
                  </select>
                </div>

                <div className='grid grid-cols-2 gap-4'>
                  <div>
                    <label className='block text-sm font-medium text-gray-700 mb-1'>
                      Stock Mínimo
                    </label>
                    <input
                      type='number'
                      value={editForm.minimum_stock}
                      onChange={(e) =>
                        setEditForm({
                          ...editForm,
                          minimum_stock: e.target.value,
                        })
                      }
                      placeholder='Opcional'
                      className='w-full border border-gray-300 rounded-lg px-3 py-2 bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500'
                    />
                  </div>
                  <div>
                    <label className='block text-sm font-medium text-gray-700 mb-1'>
                      Stock Máximo
                    </label>
                    <input
                      type='number'
                      value={editForm.maximum_stock}
                      onChange={(e) =>
                        setEditForm({
                          ...editForm,
                          maximum_stock: e.target.value,
                        })
                      }
                      placeholder='Opcional'
                      className='w-full border border-gray-300 rounded-lg px-3 py-2 bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500'
                    />
                  </div>
                </div>

                <div className='flex gap-3 pt-4'>
                  <button
                    onClick={handleSubmit}
                    disabled={submitting || !editForm.name.trim()}
                    className='flex-1 bg-purple-600 text-white py-2 px-4 rounded-lg hover:bg-purple-700 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center justify-center gap-2'
                  >
                    {submitting ? (
                      <Loader2 className='h-4 w-4 animate-spin' />
                    ) : (
                      <Check className='h-4 w-4' />
                    )}
                    {submitting ? 'Guardando...' : 'Guardar Cambios'}
                  </button>
                  <button
                    onClick={handleClose}
                    className='px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50'
                  >
                    Cancelar
                  </button>
                </div>
              </div>
            ) : (
              <div className='text-center text-gray-500 py-16'>
                <Package className='h-16 w-16 mx-auto text-gray-300 mb-4' />
                <p>Selecciona un producto de la lista para editarlo</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default EditInventoryModal;
