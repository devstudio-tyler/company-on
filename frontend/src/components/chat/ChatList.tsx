'use client';

import { MessageCircle } from 'lucide-react';
import { useEffect, useRef } from 'react';
import ChatMessage, { type Source } from './ChatMessage';

export interface ChatMessageData {
  id: string;
  content: string;
  isUser: boolean;
  timestamp: Date;
  sources?: Source[];
  feedback?: 'up' | 'down' | null;
  isStreaming?: boolean;
}

interface ChatListProps {
  messages: ChatMessageData[];
  isLoading?: boolean;
  onFeedback?: (messageId: string, feedback: 'up' | 'down', comment?: string) => void;
}

export default function ChatList({ messages, isLoading = false, onFeedback }: ChatListProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 새 메시지가 추가되면 자동 스크롤
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // 로딩 상태 표시
  if (isLoading && messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="text-center">
          <div className="w-8 h-8 mx-auto mb-4">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
          <p className="text-gray-500">채팅 기록을 불러오는 중...</p>
        </div>
      </div>
    );
  }

  if (messages.length === 0 && !isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="text-center">
          <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <MessageCircle className="w-8 h-8 text-gray-400" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            새로운 대화를 시작해보세요
          </h3>
          <p className="text-gray-500 max-w-sm mx-auto">
            궁금한 것이 있으시면 아래 입력창에 질문을 입력해주세요.
            업로드된 문서를 기반으로 답변해드립니다.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto" data-chat-list>
      <div className="max-w-3xl mx-auto">
        {messages.map((message) => (
          <ChatMessage
            key={message.id}
            id={message.id}
            content={message.content}
            isUser={message.isUser}
            timestamp={message.timestamp}
            sources={message.sources}
            feedback={message.feedback}
            isStreaming={message.isStreaming}
            onFeedback={onFeedback}
          />
        ))}

        {/* 로딩 인디케이터 */}
        {isLoading && (
          <div className="flex gap-4 p-4 bg-gray-50">
            <div className="w-8 h-8 rounded-full bg-green-600 text-white flex items-center justify-center flex-shrink-0">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.847a4.5 4.5 0 003.09 3.09L15.75 12l-2.847.813a4.5 4.5 0 00-3.09 3.09z" />
              </svg>
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-1">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
              </div>
              <div className="text-xs text-gray-500 mt-1">답변을 생성하고 있습니다...</div>
            </div>
          </div>
        )}

        {/* 스크롤 앵커 */}
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
}
