'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Send, BarChart3, LogOut, User, Sparkles, Zap } from 'lucide-react';

import { ChatMessage } from '@/types/chat';
import { sendChatMessage } from '@/lib/api';
import { generateId } from '@/lib/utils';
import { MessageItem, QuickActions } from '@/components';
import CreateSaleModal from '@/components/CreateSaleModal';
import CreateProductModal from '@/components/CreateProductModal';
import EditInventoryModal from '@/components/EditInventoryModal';
import PremiumButton from '@/components/ui/PremiumButton';
import { useAuth } from '@/contexts/AuthContext';

export default function ChatInterface() {
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

  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Función simple y directa para scroll
  const scrollToBottom = () => {
    if (messagesContainerRef.current) {
      const container = messagesContainerRef.current;
      // Scroll inmediato
      container.scrollTop = container.scrollHeight;
      // Scroll con delay para asegurar que funcione
      setTimeout(() => {
        container.scrollTop = container.scrollHeight;
      }, 100);
      setTimeout(() => {
        container.scrollTop = container.scrollHeight;
      }, 500);
    }
  };

  // Scroll cuando cambian los mensajes
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Scroll adicional cuando cambia el número de mensajes
  useEffect(() => {
    const timer = setTimeout(scrollToBottom, 1000);
    return () => clearTimeout(timer);
  }, [messages.length]);

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

    // Scroll después de agregar mensajes
    setTimeout(scrollToBottom, 100);

    try {
      const response = await sendChatMessage({
        message: messageText,
        context: {},
      });

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

      // Scroll después de recibir respuesta
      setTimeout(scrollToBottom, 200);
      setTimeout(scrollToBottom, 1000); // Scroll adicional para contenido que se carga tarde
    } catch (error) {
      console.error('Error sending message:', error);

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
    <div className='h-full w-full flex flex-col bg-transparent'>
      {/* Header Compacto */}
      <div className='flex-shrink-0 border-b border-white/10 backdrop-blur-xl bg-white/5 p-3'>
        <div className='flex items-center justify-between'>
          <div className='flex items-center gap-3'>
            <div className='relative'>
              <div className='w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg flex items-center justify-center'>
                <BarChart3 className='h-4 w-4 text-white' />
              </div>
              <div className='absolute -top-1 -right-1 w-2 h-2 bg-green-500 rounded-full border border-white' />
            </div>
            <div>
              <h1 className='text-lg font-bold text-white flex items-center gap-1'>
                SmartStock AI
                <Sparkles className='h-3 w-3 text-yellow-400' />
              </h1>
              <p className='text-white/60 text-xs'>
                Enterprise Intelligence Platform
              </p>
            </div>
          </div>

          <div className='flex items-center gap-2'>
            <div className='flex items-center gap-1 px-2 py-1 bg-white/10 rounded-md border border-white/20'>
              <User className='h-3 w-3 text-white/70' />
              <span className='text-white/90 text-xs'>
                {user?.full_name || user?.username}
              </span>
            </div>

            <PremiumButton
              variant='ghost'
              size='sm'
              onClick={logout}
              className='text-white/70 hover:text-red-400 px-2 py-1 text-xs'
            >
              <LogOut className='h-3 w-3 mr-1' />
              Salir
            </PremiumButton>
          </div>
        </div>

        <div className='flex items-center gap-2 mt-2 text-white/50 text-xs'>
          <div className='w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse' />
          <span>Sistema de IA Activo</span>
          <Zap className='h-3 w-3 ml-1 text-yellow-400' />
          <span>Multi-Agent Architecture</span>
        </div>
      </div>

      {/* Área de Mensajes - OCUPA TODO EL ESPACIO RESTANTE */}
      <div className='flex-1 min-h-0 flex flex-col'>
        <div
          ref={messagesContainerRef}
          className='flex-1 overflow-y-auto overflow-x-hidden p-4'
          style={{
            scrollBehavior: 'smooth',
          }}
        >
          <div className='space-y-4'>
            {messages.map((message) => (
              <div key={message.id}>
                <MessageItem message={message} />
              </div>
            ))}
            <div className='h-8' />
          </div>
        </div>

        {/* Quick Actions - Siempre Visible */}
        <div className='flex-shrink-0'>
          <QuickActions
            onAction={handleQuickAction}
            onCreateSaleClick={handleCreateSaleClick}
            onCreateProductClick={handleCreateProductClick}
            onEditInventoryClick={handleEditInventoryClick}
            disabled={isLoading}
          />
        </div>

        {/* Input Area */}
        <div className='flex-shrink-0 border-t border-white/10 backdrop-blur-xl bg-white/5 p-4'>
          <div className='flex gap-3 items-end'>
            <div className='flex-1 relative'>
              <input
                ref={inputRef}
                type='text'
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder='Pregúntame sobre tu inventario, ventas o rendimiento empresarial...'
                className='w-full bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 backdrop-blur-sm transition-all duration-300 text-sm'
                disabled={isLoading}
              />
            </div>

            <PremiumButton
              onClick={() => handleSendMessage()}
              disabled={!inputValue.trim() || isLoading}
              loading={isLoading}
              glow={!!inputValue.trim()}
              className='px-4 py-3'
              size='sm'
            >
              {!isLoading && <Send className='h-4 w-4' />}
              Enviar
            </PremiumButton>
          </div>

          {/* Indicador de carga */}
          {isLoading && (
            <div className='flex items-center gap-2 mt-2 text-white/60 text-xs'>
              <div className='flex gap-1'>
                <div className='w-1 h-1 bg-blue-400 rounded-full animate-pulse' />
                <div
                  className='w-1 h-1 bg-purple-400 rounded-full animate-pulse'
                  style={{ animationDelay: '0.2s' }}
                />
                <div
                  className='w-1 h-1 bg-cyan-400 rounded-full animate-pulse'
                  style={{ animationDelay: '0.4s' }}
                />
              </div>
              <span>SmartStock AI está procesando tu solicitud...</span>
            </div>
          )}
        </div>
      </div>

      {/* Modals */}
      <CreateSaleModal
        isOpen={showSaleModal}
        onClose={() => setShowSaleModal(false)}
        onSaleCreated={handleSaleCreated}
      />

      <CreateProductModal
        isOpen={showProductModal}
        onClose={() => setShowProductModal(false)}
        onProductsCreated={handleProductsCreated}
      />

      <EditInventoryModal
        isOpen={showEditInventoryModal}
        onClose={() => setShowEditInventoryModal(false)}
        onProductEdited={handleProductEdited}
      />
    </div>
  );
}
