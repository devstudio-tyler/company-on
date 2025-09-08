'use client';

import React, { useState, useCallback, useEffect } from 'react';
import ChatList, { type ChatMessageData } from './ChatList';
import ChatInput from './ChatInput';
import { getClientId } from '@/lib/utils';

interface ChatPageProps {
  sessionId?: string;
}

export default function ChatPage({ sessionId }: ChatPageProps) {
  const [messages, setMessages] = useState<ChatMessageData[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(sessionId || null);

  // SSE 연결을 위한 EventSource 관리
  const [eventSource, setEventSource] = useState<EventSource | null>(null);

  // 컴포넌트 언마운트 시 SSE 연결 정리
  useEffect(() => {
    return () => {
      if (eventSource) {
        eventSource.close();
      }
    };
  }, [eventSource]);

  // 스트리밍 메시지 전송 처리
  const handleSendMessage = useCallback(async (content: string) => {
    const clientId = getClientId();
    
    // 사용자 메시지 즉시 추가
    const userMessage: ChatMessageData = {
      id: `user-${Date.now()}`,
      content,
      isUser: true,
      timestamp: new Date(),
    };
    
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    // AI 응답 메시지를 위한 임시 ID
    const aiMessageId = `ai-${Date.now()}`;

    try {
      // 스트리밍 API 호출
      console.log('API 요청 시작:', {
        url: '/api/v1/chat/messages/stream',
        clientId,
        content,
        sessionId: currentSessionId
      });
      
      const response = await fetch('/api/v1/chat/messages/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Client-ID': clientId,
        },
        body: JSON.stringify({
          client_id: clientId,
          content,
          session_id: currentSessionId,
          max_results: 5,
          include_history: true,
        }),
      });

      console.log('API 응답 상태:', {
        status: response.status,
        statusText: response.statusText,
        ok: response.ok,
        headers: Object.fromEntries(response.headers.entries())
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('API 응답 오류:', errorText);
        throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
      }

      if (!response.body) {
        throw new Error('Response body is null');
      }

      // AI 응답 메시지 초기 생성 (스트리밍용)
      const aiMessage: ChatMessageData = {
        id: aiMessageId,
        content: '',
        isUser: false,
        timestamp: new Date(),
        sources: [],
        isStreaming: true,
      };
      
      setMessages(prev => [...prev, aiMessage]);
      setIsLoading(false); // 스트리밍이 시작되면 로딩 해제

      // SSE 스트림 읽기
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            
            if (data === '[DONE]') {
              // 스트리밍 완료
              setMessages(prev => 
                prev.map(msg => 
                  msg.id === aiMessageId 
                    ? { ...msg, isStreaming: false }
                    : msg
                )
              );
              return;
            }

            try {
              const parsed = JSON.parse(data);
              
              if (parsed.type === 'chunk') {
                // 텍스트 청크 업데이트
                setMessages(prev => 
                  prev.map(msg => 
                    msg.id === aiMessageId 
                      ? { ...msg, content: msg.content + parsed.content }
                      : msg
                  )
                );
              } else if (parsed.type === 'sources') {
                // 출처 정보 업데이트
                setMessages(prev => 
                  prev.map(msg => 
                    msg.id === aiMessageId 
                      ? { ...msg, sources: parsed.sources }
                      : msg
                  )
                );
              } else if (parsed.type === 'complete') {
                // 스트리밍 완료
                setMessages(prev => 
                  prev.map(msg => 
                    msg.id === aiMessageId 
                      ? { ...msg, isStreaming: false }
                      : msg
                  )
                );
                
                // 메시지 ID 업데이트 (백엔드에서 실제 저장된 ID)
                if (parsed.message_id) {
                  setMessages(prev => 
                    prev.map(msg => 
                      msg.id === aiMessageId 
                        ? { ...msg, id: parsed.message_id }
                        : msg
                    )
                  );
                }
                return;
              } else if (parsed.type === 'error') {
                // 에러 처리
                console.error('스트리밍 에러:', parsed.error);
                setMessages(prev => prev.filter(msg => msg.id !== aiMessageId));
                
                const errorMessage: ChatMessageData = {
                  id: `error-${Date.now()}`,
                  content: `죄송합니다. 오류가 발생했습니다: ${parsed.error}`,
                  isUser: false,
                  timestamp: new Date(),
                };
                
                setMessages(prev => [...prev, errorMessage]);
                return;
              }
            } catch (parseError) {
              console.error('스트림 데이터 파싱 실패:', parseError);
            }
          }
        }
      }

    } catch (error) {
      console.error('메시지 전송 실패:', error);
      console.error('에러 상세:', {
        message: error instanceof Error ? error.message : String(error),
        stack: error instanceof Error ? error.stack : undefined,
        name: error instanceof Error ? error.name : undefined
      });
      
      // 스트리밍 메시지가 추가된 경우 제거
      setMessages(prev => prev.filter(msg => msg.id !== aiMessageId));
      
      // 에러 메시지 추가 (더 자세한 정보 포함)
      const errorMessage: ChatMessageData = {
        id: `error-${Date.now()}`,
        content: `죄송합니다. 메시지 전송 중 오류가 발생했습니다. ${error instanceof Error ? error.message : '다시 시도해주세요.'}`,
        isUser: false,
        timestamp: new Date(),
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  }, [currentSessionId]);

  // 피드백 처리
  const handleFeedback = useCallback(async (messageId: string, feedback: 'up' | 'down', comment?: string) => {
    try {
      const response = await fetch(`/api/v1/chat/messages/${messageId}/feedback`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message_id: messageId,
          feedback,
          comment,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // 메시지 목록에서 피드백 상태 업데이트
      setMessages(prev => 
        prev.map(msg => 
          msg.id === messageId 
            ? { ...msg, feedback } 
            : msg
        )
      );

    } catch (error) {
      console.error('피드백 전송 실패:', error);
      alert('피드백 전송에 실패했습니다. 다시 시도해주세요.');
    }
  }, []);

  return (
    <div className="h-full flex flex-col bg-gray-50">
      <ChatList 
        messages={messages} 
        isLoading={isLoading}
        onFeedback={handleFeedback}
      />
      <ChatInput 
        onSendMessage={handleSendMessage}
        disabled={isLoading}
      />
    </div>
  );
}
