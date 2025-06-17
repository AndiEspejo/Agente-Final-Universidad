'use client';

import React from 'react';
import { motion } from 'framer-motion';

interface FloatingParticle {
  id: number;
  x: number;
  y: number;
  size: number;
  duration: number;
}

const AnimatedBackground: React.FC = () => {
  // Generate floating particles
  const particles: FloatingParticle[] = Array.from({ length: 20 }, (_, i) => ({
    id: i,
    x: Math.random() * 100,
    y: Math.random() * 100,
    size: Math.random() * 4 + 2,
    duration: Math.random() * 20 + 10,
  }));

  return (
    <div className='fixed inset-0 overflow-hidden pointer-events-none'>
      {/* Gradient Background Principal */}
      <div className='absolute inset-0 bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900' />

      {/* Animated Gradient Overlay - Más sutil */}
      <motion.div
        className='absolute inset-0 opacity-20'
        animate={{
          background: [
            'radial-gradient(circle at 20% 50%, #3b82f6 0%, transparent 60%)',
            'radial-gradient(circle at 80% 20%, #8b5cf6 0%, transparent 60%)',
            'radial-gradient(circle at 40% 80%, #06b6d4 0%, transparent 60%)',
            'radial-gradient(circle at 20% 50%, #3b82f6 0%, transparent 60%)',
          ],
        }}
        transition={{
          duration: 15,
          repeat: Infinity,
          ease: 'linear',
        }}
      />

      {/* Floating Particles - Reducidas */}
      {particles.slice(0, 10).map((particle) => (
        <motion.div
          key={particle.id}
          className='absolute rounded-full bg-white/5 backdrop-blur-sm'
          style={{
            left: `${particle.x}%`,
            top: `${particle.y}%`,
            width: particle.size,
            height: particle.size,
          }}
          animate={{
            y: [0, -20, 0],
            x: [0, 10, 0],
            opacity: [0.2, 0.5, 0.2],
          }}
          transition={{
            duration: particle.duration,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
        />
      ))}

      {/* Grid Pattern - Más sutil */}
      <div className='absolute inset-0 opacity-3'>
        <div className='h-full w-full bg-[linear-gradient(rgba(255,255,255,0.05)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.05)_1px,transparent_1px)] bg-[size:60px_60px]' />
      </div>
    </div>
  );
};

export default AnimatedBackground;
