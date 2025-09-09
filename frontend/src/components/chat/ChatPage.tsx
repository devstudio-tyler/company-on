'use client';

import { getSessionMessages, updateSessionTitle } from '@/lib/api/sessions';
import { getClientId } from '@/lib/utils';
import { useCallback, useEffect, useState } from 'react';
import { flushSync } from 'react-dom';
import ChatInput from './ChatInput';
import ChatList, { type ChatMessageData } from './ChatList';

interface ChatPageProps {
  sessionId?: string;
}

export default function ChatPage({ sessionId }: ChatPageProps) {
  const [messages, setMessages] = useState<ChatMessageData[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(sessionId || null);
  const [isLoadingMessages, setIsLoadingMessages] = useState(false);
  const [isSendingMessage, setIsSendingMessage] = useState(false);

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

  // 세션별 메시지 로딩
  const loadSessionMessages = useCallback(async (sessionId: string) => {
    if (!sessionId) return;

    try {
      setIsLoadingMessages(true);
      const response = await getSessionMessages(sessionId);

      // API 응답을 ChatMessageData 형식으로 변환
      const loadedMessages: ChatMessageData[] = response.messages.map(msg => ({
        id: msg.id,
        content: msg.content,
        isUser: msg.is_user,
        timestamp: new Date(msg.created_at),
        sources: msg.sources || [],
        feedback: undefined, // API에서 피드백 정보가 없으므로 undefined
        isStreaming: false
      }));

      setMessages(loadedMessages);
    } catch (error) {
      console.error('메시지 로딩 실패:', error);
      // 404 오류는 새 세션이므로 빈 메시지 배열로 초기화
      if (error instanceof Error && error.message.includes('404')) {
        console.log('새 세션으로 인식하여 메시지를 빈 배열로 초기화');
        setMessages([]);
      } else {
        setMessages([]);
      }
    } finally {
      setIsLoadingMessages(false);
    }
  }, []);

  // sessionId prop이 변경될 때 currentSessionId 업데이트
  useEffect(() => {
    setCurrentSessionId(sessionId || null);
  }, [sessionId]);

  // 세션 ID가 변경될 때 메시지 로딩
  useEffect(() => {
    if (currentSessionId) {
      loadSessionMessages(currentSessionId);
    } else {
      setMessages([]);
    }
  }, [currentSessionId, loadSessionMessages]);

  // 첫 메시지 기반으로 세션 제목 자동 생성
  const generateSessionTitle = useCallback((firstMessage: string): string => {
    // 메시지가 너무 길면 앞부분만 사용
    const truncatedMessage = firstMessage.length > 30 ? firstMessage.substring(0, 30) + '...' : firstMessage;
    return truncatedMessage;
  }, []);

  // 세션 제목 업데이트
  const updateSessionTitleFromMessage = useCallback(async (sessionId: string, message: string) => {
    try {
      const newTitle = generateSessionTitle(message);
      const clientId = getClientId();
      await updateSessionTitle(sessionId, newTitle, clientId);

      // 부모 컴포넌트에 세션 업데이트 알림 (Layout에서 처리)
      window.dispatchEvent(new CustomEvent('sessionUpdated', {
        detail: { sessionId, title: newTitle }
      }));
    } catch (error) {
      console.error('세션 제목 업데이트 실패:', error);
    }
  }, [generateSessionTitle]);

  // 스트리밍 메시지 전송 처리
  const handleSendMessage = useCallback(async (content: string) => {
    // 중복 전송 방지
    if (isSendingMessage) {
      console.log('메시지 전송 중이므로 무시합니다.');
      return;
    }

    setIsSendingMessage(true);
    const clientId = getClientId();
    let sessionId = currentSessionId;

    // 세션이 없는 경우 자동으로 새 세션 생성
    if (!sessionId) {
      try {
        const { createNewSession } = await import('@/lib/api/sessions');
        const newSession = await createNewSession(clientId, `${new Date().toLocaleDateString('ko-KR')}의 새 채팅`);
        sessionId = newSession.id;
        setCurrentSessionId(sessionId);

        // 부모 컴포넌트에 새 세션 알림
        window.dispatchEvent(new CustomEvent('sessionCreated', {
          detail: { session: newSession }
        }));
      } catch (error) {
        console.error('자동 세션 생성 실패:', error);
        alert('세션 생성에 실패했습니다.');
        setIsSendingMessage(false);
        return;
      }
    }

    // 로딩 상태 시작 (메시지는 답변 완성 시점에 추가)
    setIsLoading(true);

    // AI 응답 메시지를 위한 임시 ID
    const aiMessageId = `ai-${Date.now()}`;

    try {
      // 스트리밍 API 호출
      console.log('API 요청 시작:', {
        url: '/api/v1/chat/messages/stream',
        clientId,
        content,
        sessionId
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
          session_id: sessionId,
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
        console.error('API 응답 오류 상세:', {
          status: response.status,
          statusText: response.statusText,
          url: response.url,
          headers: Object.fromEntries(response.headers.entries()),
          body: errorText
        });

        let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        try {
          const errorData = JSON.parse(errorText);
          if (errorData.detail) {
            errorMessage += ` - ${errorData.detail}`;
          }
        } catch (e) {
          if (errorText) {
            errorMessage += ` - ${errorText}`;
          }
        }

        throw new Error(errorMessage);
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

      try {
        while (true) {
          const { value, done } = await reader.read();
          if (done) {
            console.log('📡 스트림 읽기 완료');
            break;
          }

          const chunk = decoder.decode(value, { stream: true });
          console.log('📡 원시 청크 수신:', chunk);
          buffer += chunk;
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
                  // 텍스트 청크 업데이트 (디버깅 로그 추가)
                  console.log('🔥 실시간 청크 수신:', parsed.content);

                  // 즉시 상태 업데이트 (React 배칭 방지 - flushSync 사용)
                  flushSync(() => {
                    setMessages(prev => {
                      const newMessages = [...prev];
                      const messageIndex = newMessages.findIndex(msg => msg.id === aiMessageId);
                      if (messageIndex !== -1) {
                        newMessages[messageIndex] = {
                          ...newMessages[messageIndex],
                          content: newMessages[messageIndex].content + parsed.content
                        };
                      }
                      return newMessages;
                    });
                  });

                  // 즉시 스크롤 업데이트 (flushSync 후)
                  const chatContainer = document.querySelector('[data-chat-list]');
                  if (chatContainer) {
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                  }
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
                  // 스트리밍 완료 - 사용자 메시지와 AI 메시지 모두 추가
                  const userMessage: ChatMessageData = {
                    id: `user-${Date.now()}`,
                    content,
                    isUser: true,
                    timestamp: new Date(),
                  };

                  setMessages(prev => {
                    // 기존 AI 메시지 업데이트
                    const updatedMessages = prev.map(msg =>
                      msg.id === aiMessageId
                        ? { ...msg, isStreaming: false }
                        : msg
                    );

                    // 사용자 메시지를 AI 메시지 앞에 추가
                    return [userMessage, ...updatedMessages];
                  });

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

                  // 메시지 전송 완료
                  setIsSendingMessage(false);

                  // 첫 메시지인 경우 응답 내용으로 세션 제목 업데이트
                  if (currentSessionId && messages.length === 1) {
                    const aiMessage = messages.find(msg => msg.id === aiMessageId);
                    if (aiMessage && aiMessage.content) {
                      // 응답 내용을 간단히 요약하여 제목으로 설정
                      const summary = aiMessage.content.length > 50
                        ? aiMessage.content.substring(0, 50) + '...'
                        : aiMessage.content;
                      updateSessionTitleFromMessage(currentSessionId, summary);
                    }
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
      } catch (streamError) {
        console.error('스트림 읽기 중 오류:', streamError);
        console.error('스트림 오류 상세:', {
          message: streamError instanceof Error ? streamError.message : String(streamError),
          stack: streamError instanceof Error ? streamError.stack : undefined,
          name: streamError instanceof Error ? streamError.name : undefined
        });

        // 사용자 메시지 추가
        const userMessage: ChatMessageData = {
          id: `user-${Date.now()}`,
          content,
          isUser: true,
          timestamp: new Date(),
        };

        // 스트리밍 메시지가 추가된 경우 제거하고 사용자 메시지 추가
        setMessages(prev => {
          const filteredMessages = prev.filter(msg => msg.id !== aiMessageId);
          return [userMessage, ...filteredMessages];
        });

        // 스트림 오류 메시지 추가
        const streamErrorMessage: ChatMessageData = {
          id: `stream-error-${Date.now()}`,
          content: `스트리밍 중 오류가 발생했습니다: ${streamError instanceof Error ? streamError.message : '알 수 없는 오류'}`,
          isUser: false,
          timestamp: new Date(),
        };

        setMessages(prev => [...prev, streamErrorMessage]);
        setIsSendingMessage(false);
        return;
      }

    } catch (error) {
      console.error('메시지 전송 실패:', error);
      console.error('에러 상세:', {
        message: error instanceof Error ? error.message : String(error),
        stack: error instanceof Error ? error.stack : undefined,
        name: error instanceof Error ? error.name : undefined
      });

      // 사용자 메시지 추가
      const userMessage: ChatMessageData = {
        id: `user-${Date.now()}`,
        content,
        isUser: true,
        timestamp: new Date(),
      };

      // 스트리밍 메시지가 추가된 경우 제거하고 사용자 메시지 추가
      setMessages(prev => {
        const filteredMessages = prev.filter(msg => msg.id !== aiMessageId);
        return [userMessage, ...filteredMessages];
      });

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
      setIsSendingMessage(false);
    }
  }, [currentSessionId, isSendingMessage]);

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
        isLoading={isLoading || isLoadingMessages}
        onFeedback={handleFeedback}
      />
      <ChatInput
        onSendMessage={handleSendMessage}
        disabled={isLoading || isLoadingMessages}
      />
    </div>
  );
}
