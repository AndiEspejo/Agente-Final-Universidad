'use client';

import React, { useState, useEffect } from 'react';
import {
  X,
  ShoppingCart,
  AlertTriangle,
  Loader2,
  AlertCircle,
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

interface CartItem {
  product_id: number;
  quantity: number;
  name: string;
  price: number;
  subtotal: number;
  stock_quantity: number;
}

interface CreateSaleModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSaleCreated: (message: string) => void;
}

const CreateSaleModal: React.FC<CreateSaleModalProps> = ({
  isOpen,
  onClose,
  onSaleCreated,
}) => {
  const [products, setProducts] = useState<Product[]>([]);
  const [cart, setCart] = useState<CartItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [customerName, setCustomerName] = useState('');
  const [paymentMethod, setPaymentMethod] = useState('credit_card');

  // Auto-hide error messages after 4 seconds
  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => {
        setError(null);
      }, 4000);

      return () => clearTimeout(timer);
    }
  }, [error]);

  // Load products when modal opens
  useEffect(() => {
    if (isOpen) {
      loadProducts();
      setCart([]);
      setCustomerName('');
      setError(null);
    }
  }, [isOpen]);

  const loadProducts = async () => {
    setLoading(true);
    try {
      const token = Cookies.get('auth_token');
      console.log(
        'Loading products with token:',
        token ? 'present' : 'missing'
      );

      const API_BASE_URL =
        process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const url = `${API_BASE_URL}/inventory/products-with-stock`;
      console.log('Fetching from URL:', url);

      const response = await fetch(url, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      console.log('Response status:', response.status);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Response error:', errorText);
        throw new Error(
          `HTTP ${response.status}: ${errorText || 'Error cargando productos'}`
        );
      }

      const data = await response.json();
      console.log('Products loaded:', data.products?.length || 0);
      setProducts(data.products || []);
    } catch (err) {
      const errorMessage =
        err instanceof Error
          ? err.message
          : 'Error cargando productos disponibles';
      setError(errorMessage);
      console.error('Error loading products:', err);
    } finally {
      setLoading(false);
    }
  };

  const addToCart = (product: Product) => {
    const existingItem = cart.find((item) => item.product_id === product.id);

    if (existingItem) {
      updateQuantity(product.id, existingItem.quantity + 1);
    } else {
      const newItem: CartItem = {
        product_id: product.id,
        quantity: 1,
        name: product.name,
        price: product.price,
        subtotal: product.price,
        stock_quantity: product.stock_quantity,
      };
      setCart([...cart, newItem]);
    }
  };

  const updateQuantity = (productId: number, newQuantity: number) => {
    if (newQuantity <= 0) {
      removeFromCart(productId);
      return;
    }

    const product = products.find((p) => p.id === productId);
    if (!product) return;

    if (newQuantity > product.stock_quantity) {
      setError(
        `Stock insuficiente para ${product.name}. Máximo disponible: ${product.stock_quantity}`
      );
      return;
    }

    setCart(
      cart.map((item) =>
        item.product_id === productId
          ? {
              ...item,
              quantity: newQuantity,
              subtotal: item.price * newQuantity,
            }
          : item
      )
    );
    setError(null);
  };

  const removeFromCart = (productId: number) => {
    setCart(cart.filter((item) => item.product_id !== productId));
  };

  const getTotalAmount = () => {
    return cart.reduce((total, item) => total + item.subtotal, 0);
  };

  const handleSubmit = async () => {
    if (cart.length === 0) {
      setError('Agrega al menos un producto al carrito');
      return;
    }

    if (!customerName.trim()) {
      setError('Ingresa el nombre del cliente');
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const token = Cookies.get('auth_token');

      const orderData = {
        customer_name: customerName,
        items: cart.map((item) => ({
          product_id: item.product_id,
          quantity: item.quantity,
        })),
        payment_method: paymentMethod,
      };

      const API_BASE_URL =
        process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(
        `${API_BASE_URL}/sales/create-order-with-inventory-sync`,
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(orderData),
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Error creando orden de venta');
      }

      const result = await response.json();

      // Notify parent component
      const inventoryUpdates =
        result.inventory_updates && Array.isArray(result.inventory_updates)
          ? result.inventory_updates
              .map(
                (update: {
                  product_name: string;
                  previous_quantity: number;
                  new_quantity: number;
                  quantity_sold: number;
                }) =>
                  `• ${update.product_name}: ${update.previous_quantity} → ${update.new_quantity} (-${update.quantity_sold})`
              )
              .join('\n')
          : 'Inventario actualizado correctamente';

      const message = `🎉 **¡Venta Creada Exitosamente!**\n\n**Orden:** ${
        result.order?.order_number || 'N/A'
      }\n**Total:** $${(result.order?.total_amount || 0).toFixed(
        2
      )}\n**Productos:** ${
        result.order?.items_count || cart.length
      }\n\n**Inventario Actualizado:**\n${inventoryUpdates}`;

      onSaleCreated(message);
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Error creando la venta');
    } finally {
      setSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className='fixed inset-0 backdrop-blur-sm bg-black/30 flex items-center justify-center z-50 p-4'>
      <div className='relative backdrop-blur-xl bg-slate-900/90 border border-white/20 rounded-2xl shadow-2xl max-w-6xl w-full max-h-[90vh] overflow-hidden'>
        {/* Fondo gradiente interno */}
        <div className='absolute inset-0 rounded-2xl bg-gradient-to-br from-slate-800/50 via-purple-900/30 to-slate-800/50' />

        {/* Header */}
        <div className='relative z-10 flex items-center justify-between p-6 border-b border-white/10'>
          <h2 className='text-2xl font-bold text-white flex items-center gap-2'>
            <ShoppingCart className='w-6 h-6 text-blue-400' />
            Crear Nueva Venta
          </h2>
          <button
            onClick={onClose}
            className='text-white/70 hover:text-white transition-colors p-2 hover:bg-white/10 rounded-lg'
          >
            <X className='w-6 h-6' />
          </button>
        </div>

        {/* Content */}
        <div className='relative z-10 flex h-[calc(90vh-140px)]'>
          {/* Products List */}
          <div className='flex-1 p-6 overflow-y-auto border-r border-white/10'>
            <h3 className='text-lg font-semibold mb-4 text-white'>
              Productos Disponibles
            </h3>

            {loading ? (
              <div className='flex items-center justify-center py-12'>
                <Loader2 className='h-8 w-8 animate-spin text-blue-400' />
                <span className='ml-2 text-white/70'>
                  Cargando productos...
                </span>
              </div>
            ) : (
              <div className='space-y-3'>
                {products.map((product, index) => (
                  <div
                    key={product.id || product.sku || `product-${index}`}
                    className={`p-4 border border-white/20 rounded-lg ${
                      product.available_for_sale
                        ? 'bg-white/10 hover:bg-white/20'
                        : 'bg-red-500/20 opacity-60'
                    }`}
                  >
                    <div className='flex items-center justify-between'>
                      <div className='flex-1'>
                        <div className='flex items-center gap-2 mb-1'>
                          <h4 className='font-semibold text-white'>
                            {product.name}
                          </h4>
                          <span className='text-sm text-white/70'>
                            ({product.sku})
                          </span>
                        </div>
                        <div className='flex items-center gap-4 text-sm text-white/70'>
                          <span className='font-medium'>
                            ${product.price.toFixed(2)}
                          </span>
                          <span>{product.category}</span>
                          <span>{product.location}</span>
                        </div>
                        <div className='flex items-center gap-4 text-sm text-white/80'>
                          <span>Stock: {product.stock_quantity}</span>
                          {product.stock_quantity <= 5 && (
                            <span className='text-red-400 font-medium flex items-center gap-1'>
                              <AlertTriangle className='h-4 w-4' />
                              {product.stock_quantity === 1
                                ? 'Stock crítico'
                                : 'Stock bajo'}
                            </span>
                          )}
                        </div>
                      </div>

                      <button
                        onClick={() => addToCart(product)}
                        disabled={!product.available_for_sale}
                        className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-300 ${
                          product.available_for_sale
                            ? 'bg-blue-500 text-white hover:bg-blue-600 shadow-lg'
                            : 'bg-red-500/30 text-red-300 cursor-not-allowed border border-red-500/50'
                        }`}
                      >
                        {product.available_for_sale ? '+' : 'Sin Stock'}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Cart */}
          <div className='w-96 p-6 bg-white/5 border-l border-white/10'>
            <h3 className='text-lg font-semibold mb-4 text-white'>
              Carrito de Compras
            </h3>

            {/* Customer and Payment */}
            <div className='space-y-4 mb-6'>
              <div>
                <label className='block text-sm font-medium text-white mb-1'>
                  Nombre del Cliente
                </label>
                <input
                  type='text'
                  value={customerName}
                  onChange={(e) => setCustomerName(e.target.value)}
                  className='w-full px-3 py-2 bg-white/10 border border-white/20 rounded-md text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-blue-500/50'
                  placeholder='Ej: Juan Pérez'
                />
              </div>

              <div>
                <label className='block text-sm font-medium text-white mb-1'>
                  Método de Pago
                </label>
                <select
                  value={paymentMethod}
                  onChange={(e) => setPaymentMethod(e.target.value)}
                  className='w-full px-3 py-2 bg-white/10 border border-white/20 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50'
                >
                  <option value='credit_card'>Tarjeta de Crédito</option>
                  <option value='debit_card'>Tarjeta de Débito</option>
                  <option value='cash'>Efectivo</option>
                  <option value='transfer'>Transferencia</option>
                </select>
              </div>
            </div>

            {/* Cart Items */}
            <div className='space-y-3 mb-6'>
              {cart.length === 0 ? (
                <p className='text-white/60 text-center py-8'>Carrito vacío</p>
              ) : (
                cart.map((item, index) => (
                  <div
                    key={item.product_id || `cart-item-${index}`}
                    className='bg-white/10 p-3 rounded-lg border border-white/20'
                  >
                    <div className='flex items-center justify-between mb-2'>
                      <h4 className='font-medium text-white text-sm'>
                        {item.name}
                      </h4>
                      <button
                        onClick={() => removeFromCart(item.product_id)}
                        className='text-red-400 hover:text-red-300 p-1 rounded hover:bg-red-500/20 transition-colors'
                      >
                        <X className='w-4 h-4' />
                      </button>
                    </div>

                    <div className='flex items-center justify-between'>
                      <div className='flex items-center gap-2'>
                        <button
                          onClick={() =>
                            updateQuantity(item.product_id, item.quantity - 1)
                          }
                          className='w-6 h-6 flex items-center justify-center bg-white/20 rounded text-white hover:bg-white/30'
                        >
                          -
                        </button>
                        <span className='w-8 text-center font-medium text-white'>
                          {item.quantity}
                        </span>
                        <button
                          onClick={() =>
                            updateQuantity(item.product_id, item.quantity + 1)
                          }
                          className='w-6 h-6 flex items-center justify-center bg-white/20 rounded text-white hover:bg-white/30'
                        >
                          +
                        </button>
                      </div>
                      <span className='font-medium text-white'>
                        ${item.subtotal.toFixed(2)}
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* Total */}
            <div className='border-t border-white/20 pt-4 mb-6'>
              <div className='flex justify-between items-center text-lg font-bold'>
                <span className='text-white'>Total:</span>
                <span className='text-white'>
                  ${getTotalAmount().toFixed(2)}
                </span>
              </div>
            </div>

            {/* Error Message */}
            {error && (
              <div className='mb-4 p-3 bg-red-500/20 border border-red-500/30 rounded-lg flex items-start space-x-2'>
                <AlertCircle className='h-4 w-4 text-red-400 mt-0.5 flex-shrink-0' />
                <p className='text-red-300 text-sm'>{error}</p>
              </div>
            )}

            {/* Actions */}
            <div className='space-y-3'>
              <button
                onClick={handleSubmit}
                disabled={cart.length === 0 || submitting}
                className='w-full bg-gradient-to-r from-green-500 to-emerald-600 text-white py-3 px-4 rounded-xl font-medium hover:from-green-600 hover:to-emerald-700 disabled:from-gray-500 disabled:to-gray-600 disabled:cursor-not-allowed transition-all duration-300 shadow-lg'
              >
                {submitting ? (
                  <div className='flex items-center justify-center gap-2'>
                    <Loader2 className='h-4 w-4 animate-spin' />
                    Creando...
                  </div>
                ) : (
                  'Crear Venta'
                )}
              </button>

              <button
                onClick={onClose}
                className='w-full bg-white/10 border border-white/20 text-white py-3 px-4 rounded-xl font-medium hover:bg-white/20 transition-all duration-300'
              >
                Cancelar
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CreateSaleModal;
