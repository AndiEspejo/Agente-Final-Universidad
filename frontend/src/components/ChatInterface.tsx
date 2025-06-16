'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2, BarChart3, LogOut, User } from 'lucide-react';
import { ChatMessage } from '@/types/chat';
import { sendChatMessage } from '@/lib/api';
import { cn, generateId } from '@/lib/utils';
import { MessageItem, QuickActions } from '@/components';
import CreateSaleModal from '@/components/CreateSaleModal';
import CreateProductModal from '@/components/CreateProductModal';
import EditInventoryModal from '@/components/EditInventoryModal';
import { useAuth } from '@/contexts/AuthContext';

interface ChatInterfaceProps {
  className?: string;
}

export default function ChatInterface({ className }: ChatInterfaceProps) {
  const { user, logout } = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: generateId(),
      role: 'assistant',
      content: `¡Bienvenido a SmartStock AI! 🚀

**Transformando la Gestión de Inventario** con inteligencia artificial avanzada.

Te puedo ayudar con:
• 📦 **Análisis de Inventario** - Niveles de stock, predicción de demanda, recomendaciones de reabastecimiento
• 📊 **Análisis de Ventas** - Seguimiento de rendimiento, insights de clientes, análisis de ingresos
• 🏢 **Revisiones de Negocio** - Reportes completos de inteligencia empresarial

Prueba preguntándome cosas como:
- "Ejecuta un análisis de inventario"
- "Muéstrame el rendimiento de ventas"
- "Genera un reporte de negocio"
- "¿Qué productos necesitan reabastecimiento?"

¿Qué te gustaría analizar hoy?`,
      timestamp: new Date(),
    },
  ]);

  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showSaleModal, setShowSaleModal] = useState(false);
  const [showProductModal, setShowProductModal] = useState(false);
  const [showEditInventoryModal, setShowEditInventoryModal] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (message?: string) => {
    const messageText = message || inputValue.trim();
    if (!messageText || isLoading) return;

    const userMessage: ChatMessage = {
      id: generateId(),
      role: 'user',
      content: messageText,
      timestamp: new Date(),
    };

    const loadingMessage: ChatMessage = {
      id: generateId(),
      role: 'assistant',
      content: 'Analizando tu solicitud...',
      timestamp: new Date(),
      loading: true,
    };

    setMessages((prev) => [...prev, userMessage, loadingMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const response = await sendChatMessage({
        message: messageText,
        context: {},
      });

      // Remove loading message and add actual response
      setMessages((prev) => {
        const withoutLoading = prev.slice(0, -1);
        const assistantMessage: ChatMessage = {
          id: generateId(),
          role: 'assistant',
          content: response.response,
          timestamp: new Date(),
          data: response.data,
          charts: response.charts,
          workflow_id: response.workflow_id,
        };
        return [...withoutLoading, assistantMessage];
      });
    } catch (error) {
      console.error('Error sending message:', error);

      // Remove loading message and add error message
      setMessages((prev) => {
        const withoutLoading = prev.slice(0, -1);
        const errorMessage: ChatMessage = {
          id: generateId(),
          role: 'assistant',
          content: `Lo siento, ocurrió un error: ${
            error instanceof Error ? error.message : 'Error desconocido'
          }. Por favor, inténtalo de nuevo.`,
          timestamp: new Date(),
        };
        return [...withoutLoading, errorMessage];
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleQuickAction = (message: string) => {
    handleSendMessage(message);
  };

  const handleCreateSaleClick = () => {
    setShowSaleModal(true);
  };

  const handleCreateProductClick = () => {
    setShowProductModal(true);
  };

  const handleEditInventoryClick = () => {
    setShowEditInventoryModal(true);
  };

  const handleSaleCreated = (message: string) => {
    const assistantMessage: ChatMessage = {
      id: generateId(),
      role: 'assistant',
      content: message,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, assistantMessage]);
  };

  const handleProductsCreated = (message: string) => {
    const assistantMessage: ChatMessage = {
      id: generateId(),
      role: 'assistant',
      content: message,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, assistantMessage]);
  };

  const handleProductEdited = (message: string) => {
    const assistantMessage: ChatMessage = {
      id: generateId(),
      role: 'assistant',
      content: message,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, assistantMessage]);
  };

  return (
    <div className={cn('flex flex-col h-full bg-white', className)}>
      {/* Header */}
      <div className='border-b border-gray-200 p-4'>
        <div className='flex items-center justify-between'>
          <div>
            <h1 className='text-xl font-semibold text-gray-900 flex items-center gap-2'>
              <BarChart3 className='h-6 w-6 text-blue-600' />
              SmartStock AI
            </h1>
            <p className='text-sm text-gray-600 mt-1'>
              Transformando la Gestión de Inventario
            </p>
          </div>

          <div className='flex items-center gap-3'>
            <div className='flex items-center gap-2 text-sm text-gray-600'>
              <User className='h-4 w-4' />
              <span>{user?.full_name || user?.username}</span>
            </div>
            <button
              onClick={logout}
              className='flex items-center gap-2 px-3 py-2 text-sm text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors'
              title='Cerrar sesión'
            >
              <LogOut className='h-4 w-4' />
              Salir
            </button>
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <div className='flex-1 overflow-y-auto p-4 space-y-4'>
        {messages.map((message) => (
          <MessageItem key={message.id} message={message} />
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Quick Actions */}
      <QuickActions
        onAction={handleQuickAction}
        onCreateSaleClick={handleCreateSaleClick}
        onCreateProductClick={handleCreateProductClick}
        onEditInventoryClick={handleEditInventoryClick}
        disabled={isLoading}
      />

      {/* Input Area */}
      <div className='border-t border-gray-200 p-4'>
        <div className='flex gap-3'>
          <input
            ref={inputRef}
            type='text'
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder='Pregúntame sobre tu inventario, ventas o rendimiento empresarial...'
            className='flex-1 border border-gray-300 rounded-lg px-4 py-2 text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            disabled={isLoading}
          />
          <button
            onClick={() => handleSendMessage()}
            disabled={!inputValue.trim() || isLoading}
            className={cn(
              'px-4 py-2 rounded-lg font-medium transition-colors flex items-center gap-2',
              inputValue.trim() && !isLoading
                ? 'bg-blue-600 text-white hover:bg-blue-700'
                : 'bg-gray-300 text-gray-500 cursor-not-allowed'
            )}
          >
            {isLoading ? (
              <Loader2 className='h-4 w-4 animate-spin' />
            ) : (
              <Send className='h-4 w-4' />
            )}
            Enviar
          </button>
        </div>
      </div>

      {/* Create Sale Modal */}
      <CreateSaleModal
        isOpen={showSaleModal}
        onClose={() => setShowSaleModal(false)}
        onSaleCreated={handleSaleCreated}
      />

      {/* Create Product Modal */}
      <CreateProductModal
        isOpen={showProductModal}
        onClose={() => setShowProductModal(false)}
        onProductsCreated={handleProductsCreated}
      />

      {/* Edit Inventory Modal */}
      <EditInventoryModal
        isOpen={showEditInventoryModal}
        onClose={() => setShowEditInventoryModal(false)}
        onProductEdited={handleProductEdited}
      />
    </div>
  );
}
