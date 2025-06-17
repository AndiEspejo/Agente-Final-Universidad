'use client';

import React from 'react';

import { cn } from '@/lib/utils';

interface GlassCardProps {
  children: React.ReactNode;
  className?: string;
  hover?: boolean;
  glow?: boolean;
}

const GlassCard: React.FC<GlassCardProps> = ({
  children,
  className,
  hover = true,
  glow = false,
}) => {
  return (
    <div
      className={cn(
        // Base glass morphism styles con fondo más sólido
        'relative backdrop-blur-xl bg-slate-900/80 border border-white/20',
        'rounded-2xl shadow-2xl',
        // Glow effect
        glow && 'shadow-blue-500/25',
        // Hover effect
        hover && 'hover:shadow-3xl transition-shadow duration-300',
        className
      )}
    >
      {/* Fondo gradiente interno */}
      <div className='absolute inset-0 rounded-2xl bg-gradient-to-br from-slate-800/50 via-purple-900/30 to-slate-800/50' />

      {/* Borde interno sutil */}
      <div className='absolute inset-0 rounded-2xl bg-gradient-to-r from-white/5 to-transparent' />

      {/* Content */}
      <div className='relative z-10'>{children}</div>
    </div>
  );
};

export default GlassCard;
