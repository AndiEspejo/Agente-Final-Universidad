'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import LoginForm from '@/components/auth/LoginForm';
import RegisterForm from '@/components/auth/RegisterForm';

export default function AuthPage() {
  const [isLogin, setIsLogin] = useState(true);
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isAuthenticated) {
      router.push('/');
    }
  }, [isAuthenticated, router]);

  const handleAuthSuccess = () => {
    router.push('/');
  };

  const toggleMode = () => {
    setIsLogin(!isLogin);
  };

  if (isLoading) {
    return (
      <div className='min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center'>
        <div className='bg-white rounded-xl shadow-lg p-8'>
          <div className='flex items-center justify-center'>
            <div className='animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600'></div>
            <span className='ml-3 text-gray-600'>Cargando...</span>
          </div>
        </div>
      </div>
    );
  }

  if (isAuthenticated) {
    return null; // Will redirect via useEffect
  }

  return (
    <div className='min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4'>
      <div className='w-full max-w-md'>
        <div className='text-center mb-8'>
          <h1 className='text-4xl font-bold text-gray-900 mb-2'>
            🚀 LangGraph
          </h1>
          <p className='text-gray-600'>
            Asistente de Ventas e Inventario con IA
          </p>
        </div>

        {isLogin ? (
          <LoginForm onToggleMode={toggleMode} onSuccess={handleAuthSuccess} />
        ) : (
          <RegisterForm
            onToggleMode={toggleMode}
            onSuccess={handleAuthSuccess}
          />
        )}

        <div className='mt-8 text-center'>
          <p className='text-sm text-gray-500'>
            Aplicación de demostración con inteligencia artificial
          </p>
        </div>
      </div>
    </div>
  );
}
