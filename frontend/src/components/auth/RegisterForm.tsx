'use client';

import React, { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';

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
      <div className='bg-white rounded-xl shadow-lg p-8'>
        <div className='text-center mb-8'>
          <h2 className='text-3xl font-bold text-gray-900'>Crear Cuenta</h2>
          <p className='text-gray-600 mt-2'>Únete a SmartStock AI</p>
        </div>

        <form onSubmit={handleSubmit} className='space-y-6'>
          <div>
            <label
              htmlFor='fullName'
              className='block text-sm font-medium text-gray-700 mb-2'
            >
              Nombre Completo
            </label>
            <input
              type='text'
              id='fullName'
              name='fullName'
              value={formData.fullName}
              onChange={handleInputChange}
              className='w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all text-gray-900 placeholder-gray-400'
              placeholder='Tu nombre completo'
              disabled={isSubmitting || isLoading}
            />
          </div>

          <div>
            <label
              htmlFor='email'
              className='block text-sm font-medium text-gray-700 mb-2'
            >
              Email
            </label>
            <input
              type='email'
              id='email'
              name='email'
              value={formData.email}
              onChange={handleInputChange}
              className='w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all text-gray-900 placeholder-gray-400'
              placeholder='tu@email.com'
              disabled={isSubmitting || isLoading}
            />
          </div>

          <div>
            <label
              htmlFor='username'
              className='block text-sm font-medium text-gray-700 mb-2'
            >
              Nombre de Usuario
            </label>
            <input
              type='text'
              id='username'
              name='username'
              value={formData.username}
              onChange={handleInputChange}
              className='w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all text-gray-900 placeholder-gray-400'
              placeholder='usuario123'
              disabled={isSubmitting || isLoading}
            />
          </div>

          <div>
            <label
              htmlFor='password'
              className='block text-sm font-medium text-gray-700 mb-2'
            >
              Contraseña
            </label>
            <input
              type='password'
              id='password'
              name='password'
              value={formData.password}
              onChange={handleInputChange}
              className='w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all text-gray-900 placeholder-gray-400'
              placeholder='Mínimo 6 caracteres'
              disabled={isSubmitting || isLoading}
            />
          </div>

          <div>
            <label
              htmlFor='confirmPassword'
              className='block text-sm font-medium text-gray-700 mb-2'
            >
              Confirmar Contraseña
            </label>
            <input
              type='password'
              id='confirmPassword'
              name='confirmPassword'
              value={formData.confirmPassword}
              onChange={handleInputChange}
              className='w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all text-gray-900 placeholder-gray-400'
              placeholder='Repite tu contraseña'
              disabled={isSubmitting || isLoading}
            />
          </div>

          {error && (
            <div className='bg-red-50 border border-red-200 rounded-lg p-4'>
              <p className='text-red-700 text-sm'>{error}</p>
            </div>
          )}

          <button
            type='submit'
            disabled={isSubmitting || isLoading}
            className='w-full bg-green-600 hover:bg-green-700 disabled:bg-green-400 text-white font-semibold py-3 px-4 rounded-lg transition-colors duration-200 focus:ring-2 focus:ring-green-500 focus:ring-offset-2'
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
            <p className='text-gray-600'>
              ¿Ya tienes una cuenta?{' '}
              <button
                onClick={onToggleMode}
                className='text-blue-600 hover:text-blue-700 font-semibold transition-colors'
              >
                Inicia sesión aquí
              </button>
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
