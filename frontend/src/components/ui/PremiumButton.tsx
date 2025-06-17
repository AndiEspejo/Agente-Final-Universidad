'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

interface PremiumButtonProps {
  children: React.ReactNode;
  variant?: 'primary' | 'secondary' | 'success' | 'danger' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  onClick?: () => void;
  disabled?: boolean;
  loading?: boolean;
  glow?: boolean;
}

const PremiumButton: React.FC<PremiumButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  className,
  onClick,
  disabled = false,
  loading = false,
  glow = false,
}) => {
  const baseClasses =
    'relative overflow-hidden font-semibold transition-all duration-300 rounded-xl border backdrop-blur-sm';

  const variants = {
    primary:
      'bg-gradient-to-r from-blue-600 to-purple-600 text-white border-blue-500/50 hover:from-blue-500 hover:to-purple-500',
    secondary:
      'bg-gradient-to-r from-slate-600 to-slate-700 text-white border-slate-500/50 hover:from-slate-500 hover:to-slate-600',
    success:
      'bg-gradient-to-r from-emerald-600 to-green-600 text-white border-emerald-500/50 hover:from-emerald-500 hover:to-green-500',
    danger:
      'bg-gradient-to-r from-red-600 to-pink-600 text-white border-red-500/50 hover:from-red-500 hover:to-pink-500',
    ghost: 'bg-white/10 text-white border-white/20 hover:bg-white/20',
  };

  const sizes = {
    sm: 'px-4 py-2 text-sm',
    md: 'px-6 py-3 text-base',
    lg: 'px-8 py-4 text-lg',
  };

  const glowColors = {
    primary: 'shadow-blue-500/50',
    secondary: 'shadow-slate-500/50',
    success: 'shadow-emerald-500/50',
    danger: 'shadow-red-500/50',
    ghost: 'shadow-white/20',
  };

  return (
    <motion.button
      className={cn(
        baseClasses,
        variants[variant],
        sizes[size],
        glow && glowColors[variant],
        disabled && 'opacity-50 cursor-not-allowed',
        className
      )}
      onClick={onClick}
      disabled={disabled || loading}
      whileHover={!disabled ? { scale: 1.05 } : undefined}
      whileTap={!disabled ? { scale: 0.95 } : undefined}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      {/* Shimmer effect */}
      <motion.div
        className='absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent'
        initial={{ x: '-100%' }}
        animate={{ x: '100%' }}
        transition={{
          duration: 2,
          repeat: Infinity,
          repeatDelay: 3,
          ease: 'linear',
        }}
      />

      {/* Content */}
      <span className='relative z-10 flex items-center justify-center gap-2'>
        {loading && (
          <motion.div
            className='w-4 h-4 border-2 border-current border-t-transparent rounded-full'
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
          />
        )}
        {children}
      </span>

      {/* Glow effect */}
      {glow && (
        <div className='absolute inset-0 rounded-xl bg-gradient-to-r from-current/20 to-current/20 blur-xl' />
      )}
    </motion.button>
  );
};

export default PremiumButton;
