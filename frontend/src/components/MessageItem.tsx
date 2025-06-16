/* eslint-disable @typescript-eslint/no-explicit-any */
'use client';

import React from 'react';
import ReactMarkdown from 'react-markdown';
import { User, Bot, Loader2 } from 'lucide-react';
import { ChatMessage } from '@/types/chat';
import { cn, formatDate } from '@/lib/utils';
import { AnalysisDisplay, ChartDisplay } from '@/components';

interface MessageItemProps {
  message: ChatMessage;
}

export default function MessageItem({ message }: MessageItemProps) {
  const isUser = message.role === 'user';
  const isLoading = message.loading;

  return (
    <div className={cn('flex gap-3', isUser ? 'justify-end' : 'justify-start')}>
      {!isUser && (
        <div className='flex-shrink-0'>
          <div className='w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center'>
            {isLoading ? (
              <Loader2 className='h-4 w-4 text-blue-600 animate-spin' />
            ) : (
              <Bot className='h-4 w-4 text-blue-600' />
            )}
          </div>
        </div>
      )}

      <div
        className={cn(
          'max-w-[80%] rounded-lg px-4 py-3',
          isUser ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-900'
        )}
      >
        {/* Message Content */}
        <div className='space-y-2'>
          {isUser ? (
            <p className='whitespace-pre-wrap'>{message.content}</p>
          ) : (
            <div className='prose prose-sm max-w-none'>
              <ReactMarkdown
                components={{
                  p: ({ children }) => (
                    <p className='mb-2 last:mb-0'>{children}</p>
                  ),
                  ul: ({ children }) => (
                    <ul className='list-disc list-inside mb-2'>{children}</ul>
                  ),
                  li: ({ children }) => <li className='mb-1'>{children}</li>,
                  strong: ({ children }) => (
                    <strong className='font-semibold'>{children}</strong>
                  ),
                  code: ({ children }) => (
                    <code className='bg-gray-200 px-1 py-0.5 rounded text-sm font-mono'>
                      {children}
                    </code>
                  ),
                  // Evitar renderizar elementos vacíos
                  div: ({ children }) =>
                    children ? <div>{children}</div> : null,
                }}
              >
                {message.content}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {/* Enhanced Analysis Data - Check for new structure */}
        {message.data && !isUser && Object.keys(message.data).length > 0 && (
          <div className='mt-4'>
            {/* Check if it's the new enhanced inventory analysis */}
            {message.data.visualizations ? (
              <AnalysisDisplay analysisData={message.data} />
            ) : (
              /* Fallback for old analysis structure */
              <AnalysisDisplay analysisData={message.data} />
            )}
          </div>
        )}

        {/* Legacy chart structure - only for old charts not handled by AnalysisDisplay */}
        {!isUser &&
          message.charts &&
          Array.isArray(message.charts) &&
          message.charts.length > 0 &&
          !message.data?.visualizations && (
            <div className='mt-4 space-y-4'>
              {message.charts.map((chart, index) => {
                // Convert old chart structure to new visualization structure
                const visualization = {
                  type: (chart as any).type || 'bar',
                  title: (chart as any).title || `Chart ${index + 1}`,
                  data: (chart as any).chart_data || (chart as any).data || [],
                  summary: (chart as any).summary || {},
                  chart_id: `legacy_chart_${index}`,
                  priority: index + 1,
                };
                return (
                  <ChartDisplay key={index} visualizations={[visualization]} />
                );
              })}
            </div>
          )}

        {/* Timestamp and Workflow ID */}
        <div
          className={cn(
            'mt-2 text-xs opacity-70',
            isUser ? 'text-blue-100' : 'text-gray-500'
          )}
        >
          <div className='flex items-center justify-between'>
            <span>{formatDate(message.timestamp)}</span>
            {message.workflow_id && (
              <span className='font-mono'>ID: {message.workflow_id}</span>
            )}
          </div>
        </div>
      </div>

      {isUser && (
        <div className='flex-shrink-0'>
          <div className='w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center'>
            <User className='h-4 w-4 text-white' />
          </div>
        </div>
      )}
    </div>
  );
}
