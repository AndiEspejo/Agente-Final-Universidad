'use client';

import React from 'react';
import { Package, BarChart3, TrendingUp, Plus, List, Edit } from 'lucide-react';
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
    color: 'bg-green-100 text-green-700 hover:bg-green-200',
  },
  {
    icon: BarChart3,
    label: 'Rendimiento de Ventas',
    message: 'Analiza el rendimiento de ventas y insights de clientes',
    color: 'bg-blue-100 text-blue-700 hover:bg-blue-200',
  },
  {
    icon: Edit,
    label: 'Editar Inventario',
    message:
      'Editar producto: ID 1, Nombre "Nuevo Nombre", Precio $150, Cantidad 20',
    color: 'bg-purple-100 text-purple-700 hover:bg-purple-200',
  },
  {
    icon: TrendingUp,
    label: 'Crear Venta',
    message:
      'Crear una nueva orden de venta: Cliente ID 1, Producto ID 1, Cantidad 2, Precio $29.99',
    color: 'bg-orange-100 text-orange-700 hover:bg-orange-200',
  },
  {
    icon: Plus,
    label: 'Añadir Producto',
    message:
      'Añadir producto: Nombre "Laptop HP", Categoría "Electrónicos", Precio $899, Cantidad 10',
    color: 'bg-emerald-100 text-emerald-700 hover:bg-emerald-200',
  },
  {
    icon: List,
    label: 'Ver Inventario',
    message: 'Listar inventario completo con estados de stock',
    color: 'bg-slate-100 text-slate-700 hover:bg-slate-200',
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
    <div className='border-t border-gray-200 p-4'>
      <div className='mb-2'>
        <h3 className='text-sm font-medium text-gray-700'>Acciones Rápidas</h3>
      </div>
      <div className='grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2'>
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
              'flex flex-col items-center p-3 rounded-lg transition-colors text-sm font-medium',
              action.color,
              disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'
            )}
          >
            <action.icon className='h-5 w-5 mb-1' />
            <span className='text-center'>{action.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
