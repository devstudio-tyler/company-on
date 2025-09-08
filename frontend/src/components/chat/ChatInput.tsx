'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Send } from 'lucide-react';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export default function ChatInput({ 
  onSendMessage, 
  disabled = false, 
  placeholder = "무엇이든 질문해보세요..." 
}: ChatInputProps) {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // 자동 높이 조절
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${Math.min(textarea.scrollHeight, 160)}px`; // 최대 160px
    }
  }, [message]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmedMessage = message.trim();
    if (!trimmedMessage || disabled) return;
    
    onSendMessage(trimmedMessage);
    setMessage('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setMessage(e.target.value);
  };

  return (
    <div className="border-t bg-white sticky bottom-0">
      <div className="max-w-3xl mx-auto px-4 py-3">
        <form onSubmit={handleSubmit} className="relative">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled}
            className={`
              w-full resize-none rounded-2xl border border-gray-300 
              px-4 py-3 pr-14 focus:outline-none focus:ring-2 focus:ring-blue-500 
              focus:border-transparent min-h-[72px] max-h-40 overflow-y-auto
              ${disabled ? 'bg-gray-100 cursor-not-allowed' : ''}
            `}
            rows={1}
          />
          <div className="absolute right-2 bottom-2">
            <button
              type="submit"
              disabled={disabled || !message.trim()}
              className={`
                w-10 h-10 rounded-full flex items-center justify-center shadow-sm
                transition-colors duration-200
                ${
                  disabled || !message.trim()
                    ? 'bg-gray-300 cursor-not-allowed'
                    : 'bg-blue-600 hover:bg-blue-700 text-white'
                }
              `}
            >
              <Send size={16} />
            </button>
          </div>
        </form>
        <p className="text-[11px] text-gray-500 mt-2">
          개인정보나 민감정보를 입력하지 마세요. Enter로 전송, Shift+Enter로 줄바꿈
        </p>
      </div>
    </div>
  );
}
