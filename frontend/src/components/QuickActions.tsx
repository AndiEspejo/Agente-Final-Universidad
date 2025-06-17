'use client';

import React from 'react';
import {
  Package,
  BarChart3,
  TrendingUp,
  Plus,
  List,
  Edit,
  Sparkles,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface QuickActionsProps {
  onAction: (message: string) => void;
  onCreateSaleClick?: () => void;
  onCreateProductClick?: () => void;
  onEditInventoryClick?: () => void;
  disabled?: boolean;
}

const quickActions = [
  {
    icon: Package,
    label: 'Análisis de Inventario',
    message:
      'Ejecuta un análisis completo de inventario con niveles de stock y recomendaciones',
    gradient: 'from-emerald-500 to-green-600',
    glow: 'shadow-emerald-500/25',
  },
  {
    icon: BarChart3,
    label: 'Rendimiento de Ventas',
    message: 'Analiza el rendimiento de ventas y insights de clientes',
    gradient: 'from-blue-500 to-cyan-600',
    glow: 'shadow-blue-500/25',
  },
  {
    icon: Edit,
    label: 'Editar Inventario',
    message:
      'Editar producto: ID 1, Nombre "Nuevo Nombre", Precio $150, Cantidad 20',
    gradient: 'from-purple-500 to-violet-600',
    glow: 'shadow-purple-500/25',
  },
  {
    icon: TrendingUp,
    label: 'Crear Venta',
    message:
      'Crear una nueva orden de venta: Cliente ID 1, Producto ID 1, Cantidad 2, Precio $29.99',
    gradient: 'from-orange-500 to-red-600',
    glow: 'shadow-orange-500/25',
  },
  {
    icon: Plus,
    label: 'Añadir Producto',
    message:
      'Añadir producto: Nombre "Laptop HP", Categoría "Electrónicos", Precio $899, Cantidad 10',
    gradient: 'from-teal-500 to-emerald-600',
    glow: 'shadow-teal-500/25',
  },
  {
    icon: List,
    label: 'Ver Inventario',
    message: 'Listar inventario completo con estados de stock',
    gradient: 'from-slate-500 to-gray-600',
    glow: 'shadow-slate-500/25',
  },
];

export default function QuickActions({
  onAction,
  onCreateSaleClick,
  onCreateProductClick,
  onEditInventoryClick,
  disabled = false,
}: QuickActionsProps) {
  return (
    <div className='border-t border-white/10 backdrop-blur-xl bg-white/5 p-4'>
      <div className='mb-3 flex items-center gap-2'>
        <Sparkles className='h-4 w-4 text-yellow-400' />
        <h3 className='text-base font-semibold text-white'>
          Acciones Inteligentes
        </h3>
      </div>

      <div className='grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3'>
        {quickActions.map((action, index) => (
          <button
            key={index}
            onClick={() => {
              if (action.label === 'Crear Venta' && onCreateSaleClick) {
                onCreateSaleClick();
              } else if (
                action.label === 'Añadir Producto' &&
                onCreateProductClick
              ) {
                onCreateProductClick();
              } else if (
                action.label === 'Editar Inventario' &&
                onEditInventoryClick
              ) {
                onEditInventoryClick();
              } else {
                onAction(action.message);
              }
            }}
            disabled={disabled}
            className={cn(
              'relative group flex flex-col items-center p-3 rounded-xl transition-all duration-200',
              'backdrop-blur-sm bg-white/10 border border-white/20 hover:bg-white/20',
              'text-white font-medium text-xs hover:scale-105',
              action.glow,
              disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'
            )}
          >
            {/* Gradient background */}
            <div
              className={cn(
                'absolute inset-0 rounded-xl bg-gradient-to-r opacity-0 group-hover:opacity-20 transition-opacity duration-200',
                action.gradient
              )}
            />

            {/* Icon with gradient */}
            <div
              className={cn(
                'w-8 h-8 rounded-lg bg-gradient-to-r flex items-center justify-center mb-2 shadow-lg',
                action.gradient
              )}
            >
              <action.icon className='h-4 w-4 text-white' />
            </div>

            {/* Label */}
            <span className='text-center leading-tight relative z-10'>
              {action.label}
            </span>
          </button>
        ))}
      </div>

      {/* Bottom indicator */}
      <div className='flex items-center justify-center mt-3 text-white/40 text-xs'>
        <div className='w-1 h-1 bg-white/40 rounded-full mr-2' />
        <span>Selecciona una acción para comenzar</span>
      </div>
    </div>
  );
}
