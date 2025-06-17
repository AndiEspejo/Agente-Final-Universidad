'use client';

import React, { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { ChatInterface } from '@/components';
import AnimatedBackground from '@/components/ui/AnimatedBackground';

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
      <div className='fixed inset-0 overflow-hidden'>
        <AnimatedBackground />
        <div className='relative z-10 h-full flex items-center justify-center'>
          <div className='backdrop-blur-xl bg-slate-900/90 border border-white/20 rounded-2xl p-8 max-w-md mx-auto'>
            <div className='flex flex-col items-center space-y-4'>
              <div className='w-12 h-12 border-4 border-blue-500/30 rounded-full animate-spin' />
              <div className='text-center'>
                <h2 className='text-xl font-bold text-white mb-1'>
                  SmartStock AI
                </h2>
                <p className='text-white/70 text-sm'>
                  Inicializando sistema...
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className='fixed inset-0 overflow-hidden'>
      <AnimatedBackground />
      <div className='relative z-10 h-full w-full backdrop-blur-xl bg-slate-900/80 border-0'>
        <ChatInterface />
      </div>
    </div>
  );
}
