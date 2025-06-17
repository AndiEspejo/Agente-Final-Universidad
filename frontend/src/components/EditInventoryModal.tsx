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
  Trash2,
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
  const [deleting, setDeleting] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);

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
      setConfirmDelete(false);
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

  const handleDelete = async () => {
    if (!selectedProduct) return;

    if (!confirmDelete) {
      setConfirmDelete(true);
      return;
    }

    setDeleting(true);
    setError(null);

    try {
      const token = Cookies.get('auth_token');
      const API_BASE_URL =
        process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

      const response = await fetch(
        `${API_BASE_URL}/inventory/product/${selectedProduct.id}`,
        {
          method: 'DELETE',
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Error eliminando producto');
      }

      const result = await response.json();
      onProductEdited(result.message);

      // Remove the product from the list
      setProducts(products.filter((p) => p.id !== selectedProduct.id));
      setSelectedProduct(null);
      setConfirmDelete(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error desconocido');
    } finally {
      setDeleting(false);
    }
  };

  const getStockStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'crítico':
        return 'text-red-600 bg-red-50';
      case 'bajo':
        return 'text-yellow-600 bg-yellow-50';
      case 'agotado':
        return 'text-red-600 bg-red-50';
      default:
        return 'text-green-600 bg-green-50';
    }
  };

  if (!isOpen) return null;

  return (
    <div className='fixed inset-0 backdrop-blur-sm bg-black/30 flex items-center justify-center z-50 p-4'>
      <div className='relative backdrop-blur-xl bg-slate-900/90 border border-white/20 rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden'>
        <div className='absolute inset-0 rounded-2xl bg-gradient-to-br from-slate-800/50 via-purple-900/30 to-slate-800/50 pointer-events-none' />

        {/* Header */}
        <div className='relative z-10 flex items-center justify-between p-6 border-b border-white/10'>
          <h2 className='text-2xl font-bold text-white flex items-center gap-2'>
            <Edit className='w-6 h-6 text-purple-400' />
            Editar Inventario
          </h2>
          <button
            onClick={handleClose}
            className='text-white/70 hover:text-white transition-colors p-2 hover:bg-white/10 rounded-lg'
          >
            <X className='w-6 h-6' />
          </button>
        </div>

        <div className='relative z-10 flex h-[600px]'>
          {/* Product List */}
          <div className='w-1/2 border-r border-white/10'>
            <div className='p-4 border-b border-white/10'>
              <div className='relative'>
                <Search className='absolute left-3 top-1/2 transform -translate-y-1/2 text-white/60 h-4 w-4' />
                <input
                  type='text'
                  placeholder='Buscar productos...'
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className='w-full pl-10 pr-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:ring-2 focus:ring-purple-400 focus:border-purple-400'
                />
              </div>
            </div>

            <div className='overflow-y-auto h-[500px] p-4'>
              {loading ? (
                <div className='flex items-center justify-center h-32'>
                  <Loader2 className='h-6 w-6 animate-spin text-white/60' />
                  <span className='ml-2 text-white/70'>
                    Cargando productos...
                  </span>
                </div>
              ) : filteredProducts.length === 0 ? (
                <div className='text-center text-white/60 py-8'>
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
                          ? 'border-purple-400 bg-purple-500/20'
                          : 'border-white/20 hover:border-purple-300 hover:bg-white/10'
                      }`}
                    >
                      <div className='flex items-center justify-between'>
                        <div className='flex-1'>
                          <h3 className='font-medium text-white'>
                            {product.name}
                          </h3>
                          <p className='text-sm text-white/70'>
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
                        <Package className='h-5 w-5 text-white/60' />
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
                <div className='text-lg font-medium text-white mb-4'>
                  Editando: {selectedProduct.name}
                </div>

                {error && (
                  <div className='bg-red-500/20 border border-red-500/30 rounded-lg p-3 flex items-center gap-2'>
                    <AlertCircle className='h-4 w-4 text-red-400 flex-shrink-0' />
                    <span className='text-red-300 text-sm'>{error}</span>
                  </div>
                )}

                <div>
                  <label className='block text-sm font-medium text-white/80 mb-1'>
                    Nombre del Producto
                  </label>
                  <input
                    type='text'
                    value={editForm.name}
                    onChange={(e) =>
                      setEditForm({ ...editForm, name: e.target.value })
                    }
                    className='w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white placeholder-white/50 focus:ring-2 focus:ring-purple-400 focus:border-purple-400'
                  />
                </div>

                <div className='grid grid-cols-2 gap-4'>
                  <div>
                    <label className='block text-sm font-medium text-white/80 mb-1'>
                      Precio ($)
                    </label>
                    <input
                      type='number'
                      step='0.01'
                      value={editForm.price}
                      onChange={(e) =>
                        setEditForm({ ...editForm, price: e.target.value })
                      }
                      className='w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white placeholder-white/50 focus:ring-2 focus:ring-purple-400 focus:border-purple-400'
                    />
                  </div>
                  <div>
                    <label className='block text-sm font-medium text-white/80 mb-1'>
                      Cantidad
                    </label>
                    <input
                      type='number'
                      value={editForm.quantity}
                      onChange={(e) =>
                        setEditForm({ ...editForm, quantity: e.target.value })
                      }
                      className='w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white placeholder-white/50 focus:ring-2 focus:ring-purple-400 focus:border-purple-400'
                    />
                  </div>
                </div>

                <div>
                  <label className='block text-sm font-medium text-white/80 mb-1'>
                    Categoría
                  </label>
                  <select
                    value={editForm.category}
                    onChange={(e) =>
                      setEditForm({ ...editForm, category: e.target.value })
                    }
                    className='w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white focus:ring-2 focus:ring-purple-400 focus:border-purple-400'
                  >
                    {Object.values(CATEGORIES).map((category) => (
                      <option
                        key={category}
                        value={category}
                        className='bg-slate-800 text-white'
                      >
                        {category}
                      </option>
                    ))}
                  </select>
                </div>

                <div className='grid grid-cols-2 gap-4'>
                  <div>
                    <label className='block text-sm font-medium text-white/80 mb-1'>
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
                      className='w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white placeholder-white/50 focus:ring-2 focus:ring-purple-400 focus:border-purple-400'
                    />
                  </div>
                  <div>
                    <label className='block text-sm font-medium text-white/80 mb-1'>
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
                      className='w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white placeholder-white/50 focus:ring-2 focus:ring-purple-400 focus:border-purple-400'
                    />
                  </div>
                </div>

                <div className='flex gap-3 pt-4'>
                  <button
                    onClick={handleSubmit}
                    disabled={submitting || !editForm.name.trim()}
                    className={`flex-1 py-3 px-4 rounded-xl font-medium transition-all duration-300 shadow-lg flex items-center justify-center gap-2 ${
                      submitting || !editForm.name.trim()
                        ? 'bg-gray-500 text-white/40 cursor-not-allowed'
                        : 'bg-gradient-to-r from-purple-500 to-purple-600 text-white hover:from-purple-600 hover:to-purple-700'
                    }`}
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
                    className='px-4 py-3 bg-white/10 border border-white/20 text-white/80 rounded-xl hover:bg-white/20 hover:text-white transition-colors'
                  >
                    Cancelar
                  </button>
                </div>

                <div className='pt-4 border-t border-white/10 mt-6'>
                  <button
                    onClick={handleDelete}
                    disabled={deleting}
                    className={`w-full py-3 px-4 rounded-xl font-medium transition-all duration-300 shadow-lg flex items-center justify-center gap-2 ${
                      deleting
                        ? 'bg-gray-500 text-white/40 cursor-not-allowed'
                        : confirmDelete
                        ? 'bg-red-600 text-white hover:bg-red-700'
                        : 'bg-white/10 border border-red-500/30 text-red-400 hover:bg-red-500/20'
                    }`}
                  >
                    {deleting ? (
                      <Loader2 className='h-4 w-4 animate-spin' />
                    ) : (
                      <Trash2 className='h-4 w-4' />
                    )}
                    {deleting
                      ? 'Eliminando...'
                      : confirmDelete
                      ? 'Confirmar Eliminación'
                      : 'Eliminar Producto'}
                  </button>
                  {confirmDelete && (
                    <p className='text-red-300 text-xs mt-2 text-center'>
                      Esta acción no se puede deshacer
                    </p>
                  )}
                </div>
              </div>
            ) : (
              <div className='text-center text-white/60 py-16'>
                <Package className='h-16 w-16 mx-auto text-white/30 mb-4' />
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
