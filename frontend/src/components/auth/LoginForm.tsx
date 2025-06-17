'use client';

import React, { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { User, Lock, Rocket, Sparkles } from 'lucide-react';

interface LoginFormProps {
  onToggleMode?: () => void;
  onSuccess?: () => void;
}

export default function LoginForm({ onToggleMode, onSuccess }: LoginFormProps) {
  const [formData, setFormData] = useState({
    username: '',
    password: '',
  });
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { login, isLoading } = useAuth();

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
    if (error) setError('');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsSubmitting(true);

    if (!formData.username || !formData.password) {
      setError('Por favor completa todos los campos');
      setIsSubmitting(false);
      return;
    }

    try {
      const result = await login(formData.username, formData.password);

      if (result.success) {
        onSuccess?.();
      } else {
        setError(result.error || 'Error en el login');
      }
    } catch {
      setError('Error de conexión');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className='w-full max-w-md mx-auto'>
      <div className='relative backdrop-blur-xl bg-slate-900/90 border border-white/20 rounded-2xl shadow-2xl p-8 overflow-hidden'>
        {/* Gradient overlay */}
        <div className='absolute inset-0 rounded-2xl bg-gradient-to-br from-slate-800/50 via-purple-900/30 to-slate-800/50 pointer-events-none' />

        {/* Content */}
        <div className='relative z-10'>
          <div className='text-center mb-8'>
            <div className='flex items-center justify-center mb-4'>
              <div className='relative'>
                <div className='w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center shadow-lg'>
                  <Rocket className='h-8 w-8 text-white' />
                </div>
                <div className='absolute -top-1 -right-1'>
                  <Sparkles className='h-6 w-6 text-yellow-400 animate-pulse' />
                </div>
              </div>
            </div>
            <h2 className='text-3xl font-bold text-white mb-2'>
              Iniciar Sesión
            </h2>
            <p className='text-white/70'>Accede a SmartStock AI</p>
          </div>

          <form onSubmit={handleSubmit} className='space-y-6'>
            <div>
              <label
                htmlFor='username'
                className='block text-sm font-medium text-white/80 mb-2'
              >
                Usuario o Email
              </label>
              <div className='relative'>
                <div className='absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none'>
                  <User className='h-5 w-5 text-white/40' />
                </div>
                <input
                  type='text'
                  id='username'
                  name='username'
                  value={formData.username}
                  onChange={handleInputChange}
                  className='w-full pl-10 pr-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-purple-400 focus:border-purple-400 transition-all backdrop-blur-sm'
                  placeholder='Ingresa tu usuario o email'
                  disabled={isSubmitting || isLoading}
                />
              </div>
            </div>

            <div>
              <label
                htmlFor='password'
                className='block text-sm font-medium text-white/80 mb-2'
              >
                Contraseña
              </label>
              <div className='relative'>
                <div className='absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none'>
                  <Lock className='h-5 w-5 text-white/40' />
                </div>
                <input
                  type='password'
                  id='password'
                  name='password'
                  value={formData.password}
                  onChange={handleInputChange}
                  className='w-full pl-10 pr-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-purple-400 focus:border-purple-400 transition-all backdrop-blur-sm'
                  placeholder='Ingresa tu contraseña'
                  disabled={isSubmitting || isLoading}
                />
              </div>
            </div>

            {error && (
              <div className='bg-red-500/20 border border-red-500/30 rounded-lg p-4 backdrop-blur-sm'>
                <p className='text-red-300 text-sm'>{error}</p>
              </div>
            )}

            <button
              type='submit'
              disabled={isSubmitting || isLoading}
              className='w-full bg-gradient-to-r from-purple-500 to-pink-600 hover:from-purple-600 hover:to-pink-700 disabled:from-white/10 disabled:to-white/10 disabled:text-white/40 text-white font-semibold py-3 px-4 rounded-lg transition-all duration-300 focus:ring-2 focus:ring-purple-400 focus:ring-offset-2 focus:ring-offset-transparent shadow-lg hover:shadow-purple-500/25'
            >
              {isSubmitting || isLoading ? (
                <div className='flex items-center justify-center'>
                  <div className='animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2'></div>
                  Iniciando sesión...
                </div>
              ) : (
                'Iniciar Sesión'
              )}
            </button>
          </form>

          {onToggleMode && (
            <div className='mt-6 text-center'>
              <p className='text-white/70'>
                ¿No tienes una cuenta?{' '}
                <button
                  onClick={onToggleMode}
                  className='text-purple-400 hover:text-purple-300 font-semibold transition-colors'
                >
                  Regístrate aquí
                </button>
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
