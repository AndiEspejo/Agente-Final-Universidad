'use client';

import React, { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { ChatInterface } from '@/components';

export default function Home() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/auth');
    }
  }, [isAuthenticated, isLoading, router]);

  if (isLoading) {
    return (
      <main className='min-h-screen bg-gray-100 flex items-center justify-center'>
        <div className='bg-white rounded-xl shadow-lg p-8'>
          <div className='flex items-center justify-center'>
            <div className='animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600'></div>
            <span className='ml-3 text-gray-600'>Cargando...</span>
          </div>
        </div>
      </main>
    );
  }

  if (!isAuthenticated) {
    return null; // Will redirect via useEffect
  }

  return (
    <main className='min-h-screen bg-gray-100'>
      <div className='container mx-auto max-w-6xl h-screen'>
        <ChatInterface className='h-full shadow-lg' />
      </div>
    </main>
  );
}
