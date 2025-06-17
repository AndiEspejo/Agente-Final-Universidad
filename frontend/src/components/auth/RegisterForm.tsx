'use client';

import React, { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { User, Mail, Lock, UserPlus, Sparkles } from 'lucide-react';

interface RegisterFormProps {
  onToggleMode?: () => void;
  onSuccess?: () => void;
}

export default function RegisterForm({
  onToggleMode,
  onSuccess,
}: RegisterFormProps) {
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    password: '',
    confirmPassword: '',
    fullName: '',
  });
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { register, isLoading } = useAuth();

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
    if (error) setError('');
  };

  const validateForm = () => {
    if (
      !formData.email ||
      !formData.username ||
      !formData.password ||
      !formData.fullName
    ) {
      return 'Por favor completa todos los campos';
    }

    if (formData.password.length < 6) {
      return 'La contraseña debe tener al menos 6 caracteres';
    }

    if (formData.password !== formData.confirmPassword) {
      return 'Las contraseñas no coinciden';
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.email)) {
      return 'Por favor ingresa un email válido';
    }

    if (formData.username.length < 3) {
      return 'El nombre de usuario debe tener al menos 3 caracteres';
    }

    return null;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsSubmitting(true);

    const validationError = validateForm();
    if (validationError) {
      setError(validationError);
      setIsSubmitting(false);
      return;
    }

    try {
      const result = await register(
        formData.email,
        formData.username,
        formData.password,
        formData.fullName
      );

      if (result.success) {
        onSuccess?.();
      } else {
        setError(result.error || 'Error en el registro');
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
                <div className='w-16 h-16 bg-gradient-to-br from-green-500 to-emerald-600 rounded-2xl flex items-center justify-center shadow-lg'>
                  <UserPlus className='h-8 w-8 text-white' />
                </div>
                <div className='absolute -top-1 -right-1'>
                  <Sparkles className='h-6 w-6 text-yellow-400 animate-pulse' />
                </div>
              </div>
            </div>
            <h2 className='text-3xl font-bold text-white mb-2'>Crear Cuenta</h2>
            <p className='text-white/70'>Únete a SmartStock AI</p>
          </div>

          <form onSubmit={handleSubmit} className='space-y-6'>
            <div>
              <label
                htmlFor='fullName'
                className='block text-sm font-medium text-white/80 mb-2'
              >
                Nombre Completo
              </label>
              <div className='relative'>
                <div className='absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none'>
                  <User className='h-5 w-5 text-white/40' />
                </div>
                <input
                  type='text'
                  id='fullName'
                  name='fullName'
                  value={formData.fullName}
                  onChange={handleInputChange}
                  className='w-full pl-10 pr-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-emerald-400 focus:border-emerald-400 transition-all backdrop-blur-sm'
                  placeholder='Tu nombre completo'
                  disabled={isSubmitting || isLoading}
                />
              </div>
            </div>

            <div>
              <label
                htmlFor='email'
                className='block text-sm font-medium text-white/80 mb-2'
              >
                Email
              </label>
              <div className='relative'>
                <div className='absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none'>
                  <Mail className='h-5 w-5 text-white/40' />
                </div>
                <input
                  type='email'
                  id='email'
                  name='email'
                  value={formData.email}
                  onChange={handleInputChange}
                  className='w-full pl-10 pr-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-emerald-400 focus:border-emerald-400 transition-all backdrop-blur-sm'
                  placeholder='tu@email.com'
                  disabled={isSubmitting || isLoading}
                />
              </div>
            </div>

            <div>
              <label
                htmlFor='username'
                className='block text-sm font-medium text-white/80 mb-2'
              >
                Nombre de Usuario
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
                  className='w-full pl-10 pr-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-emerald-400 focus:border-emerald-400 transition-all backdrop-blur-sm'
                  placeholder='usuario123'
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
                  className='w-full pl-10 pr-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-emerald-400 focus:border-emerald-400 transition-all backdrop-blur-sm'
                  placeholder='Mínimo 6 caracteres'
                  disabled={isSubmitting || isLoading}
                />
              </div>
            </div>

            <div>
              <label
                htmlFor='confirmPassword'
                className='block text-sm font-medium text-white/80 mb-2'
              >
                Confirmar Contraseña
              </label>
              <div className='relative'>
                <div className='absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none'>
                  <Lock className='h-5 w-5 text-white/40' />
                </div>
                <input
                  type='password'
                  id='confirmPassword'
                  name='confirmPassword'
                  value={formData.confirmPassword}
                  onChange={handleInputChange}
                  className='w-full pl-10 pr-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-emerald-400 focus:border-emerald-400 transition-all backdrop-blur-sm'
                  placeholder='Repite tu contraseña'
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
              className='w-full bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 disabled:from-white/10 disabled:to-white/10 disabled:text-white/40 text-white font-semibold py-3 px-4 rounded-lg transition-all duration-300 focus:ring-2 focus:ring-emerald-400 focus:ring-offset-2 focus:ring-offset-transparent shadow-lg hover:shadow-emerald-500/25'
            >
              {isSubmitting || isLoading ? (
                <div className='flex items-center justify-center'>
                  <div className='animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2'></div>
                  Creando cuenta...
                </div>
              ) : (
                'Crear Cuenta'
              )}
            </button>
          </form>

          {onToggleMode && (
            <div className='mt-6 text-center'>
              <p className='text-white/70'>
                ¿Ya tienes una cuenta?{' '}
                <button
                  onClick={onToggleMode}
                  className='text-emerald-400 hover:text-emerald-300 font-semibold transition-colors'
                >
                  Inicia sesión aquí
                </button>
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
