'use client';

import { updateSessionTitle } from '@/lib/api/sessions';
import { getClientId } from '@/lib/utils';
import { useCallback, useEffect, useRef, useState } from 'react';
import ChatInput from './ChatInput';
import ChatList, { type ChatMessageData } from './ChatList';

interface ChatPageProps {
    sessionId?: string;
}

export default function ChatPage({ sessionId }: ChatPageProps) {
    const [messages, setMessages] = useState<ChatMessageData[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [currentSessionId, setCurrentSessionId] = useState<string | null>(sessionId || null);
    const [isSendingMessage, setIsSendingMessage] = useState(false);

    // SSE 연결을 위한 EventSource 관리
    const [eventSource, setEventSource] = useState<EventSource | null>(null);

    // 스트리밍 내용을 위한 ref (성능 최적화)
    const streamingContentRef = useRef<string>('');
    const streamingMessageIdRef = useRef<string | null>(null);
    const updateTimeoutRef = useRef<NodeJS.Timeout | null>(null);

    // 스트리밍 내용 업데이트 함수 (디바운싱 적용)
    const updateStreamingContent = useCallback((content: string) => {
        streamingContentRef.current = content;

        // 기존 타이머 취소
        if (updateTimeoutRef.current) {
            clearTimeout(updateTimeoutRef.current);
        }

        // 디바운싱: 50ms 후에 상태 업데이트
        updateTimeoutRef.current = setTimeout(() => {
            setMessages(prev =>
                prev.map(msg =>
                    msg.id === streamingMessageIdRef.current
                        ? { ...msg, content: streamingContentRef.current }
                        : msg
                )
            );
        }, 50);
    }, []);

    // 컴포넌트 언마운트 시 SSE 연결 정리
    useEffect(() => {
        return () => {
            if (eventSource) {
                eventSource.close();
            }
        };
    }, [eventSource]);

    // sessionId prop이 변경될 때 currentSessionId 업데이트
    useEffect(() => {
        setCurrentSessionId(sessionId || null);
    }, [sessionId]);

    // 첫 메시지 기반으로 세션 제목 자동 생성
    const generateSessionTitle = useCallback((firstMessage: string): string => {
        const truncatedMessage = firstMessage.length > 30 ? firstMessage.substring(0, 30) + '...' : firstMessage;
        return truncatedMessage;
    }, []);

    // 세션 제목 업데이트
    const updateSessionTitleFromMessage = useCallback(async (sessionId: string, message: string) => {
        try {
            const newTitle = generateSessionTitle(message);
            const clientId = getClientId();
            await updateSessionTitle(sessionId, newTitle, clientId);

            window.dispatchEvent(new CustomEvent('sessionUpdated', {
                detail: { sessionId, title: newTitle }
            }));
        } catch (error) {
            console.error('세션 제목 업데이트 실패:', error);
        }
    }, [generateSessionTitle]);

    // 스트리밍 메시지 전송 처리
    const handleSendMessage = useCallback(async (content: string) => {
        if (isSendingMessage) {
            console.log('메시지 전송 중이므로 무시합니다.');
            return;
        }

        if (!content.trim()) return;

        setIsSendingMessage(true);
        setIsLoading(true);

        // 사용자 메시지 즉시 추가
        const userMessage: ChatMessageData = {
            id: `user-${Date.now()}`,
            content,
            isUser: true,
            timestamp: new Date(),
        };

        setMessages(prev => [...prev, userMessage]);

        // AI 응답 메시지 ID 생성
        const aiMessageId = `ai-${Date.now()}`;

        try {
            const clientId = getClientId();
            const sessionId = currentSessionId || undefined;

            console.log('🚀 메시지 전송 시작:', {
                content,
                sessionId
            });

            // 프록시 우회: 절대 경로 사용 (SSE 안정화)
            const apiBase = process.env.NEXT_PUBLIC_API_URL || '';
            const streamUrl = apiBase
                ? `${apiBase}/api/v1/chat/messages/stream`
                : '/api/v1/chat/messages/stream';

            const response = await fetch(streamUrl, {
                method: 'POST',
                // SSE 안정화를 위한 권장 헤더 및 옵션
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'text/event-stream',
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache',
                    'X-Client-ID': clientId,
                },
                // Next 프록시를 거치지 않고 CORS로 직접 연결
                mode: 'cors',
                cache: 'no-store',
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
                content: '답변 생성 중입니다...',
                isUser: false,
                timestamp: new Date(),
                sources: [],
                isStreaming: true,
            };

            setMessages(prev => [...prev, aiMessage]);
            setIsLoading(false);

            // 스트리밍 메시지 ID 설정
            streamingMessageIdRef.current = aiMessageId;
            streamingContentRef.current = '';

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
                        console.log('📝 처리할 라인:', line);
                        if (line.startsWith('data: ')) {
                            const data = line.slice(6);
                            console.log('📦 데이터 추출:', data);

                            if (data === '[DONE]') {
                                console.log('✅ 스트리밍 완료 신호 수신');
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
                                console.log('🔍 파싱된 데이터:', parsed);

                                if (parsed.type === 'chunk') {
                                    console.log('🔥 실시간 청크 수신:', parsed.content);

                                    // 첫 번째 청크인 경우 "답변 생성 중" 메시지를 실제 내용으로 교체
                                    if (streamingContentRef.current === '') {
                                        streamingContentRef.current = parsed.content;
                                        // 첫 번째 청크는 즉시 업데이트
                                        setMessages(prev =>
                                            prev.map(msg =>
                                                msg.id === aiMessageId
                                                    ? { ...msg, content: parsed.content }
                                                    : msg
                                            )
                                        );
                                    } else {
                                        streamingContentRef.current += parsed.content;
                                        // 디바운싱된 업데이트 함수 사용
                                        updateStreamingContent(streamingContentRef.current);
                                    }
                                    console.log('📝 누적된 내용:', streamingContentRef.current);

                                    // 스크롤 업데이트
                                    requestAnimationFrame(() => {
                                        const chatContainer = document.querySelector('[data-chat-list]');
                                        if (chatContainer) {
                                            chatContainer.scrollTop = chatContainer.scrollHeight;
                                        }
                                    });
                                } else if (parsed.type === 'sources') {
                                    console.log('📚 출처 정보 수신:', parsed.sources);
                                    setMessages(prev =>
                                        prev.map(msg =>
                                            msg.id === aiMessageId
                                                ? { ...msg, sources: parsed.sources }
                                                : msg
                                        )
                                    );
                                } else if (parsed.type === 'complete') {
                                    console.log('🏁 스트리밍 완료 수신');
                                    if (updateTimeoutRef.current) {
                                        clearTimeout(updateTimeoutRef.current);
                                    }

                                    // 하나의 setState 안에서 최종 콘텐츠 반영과 ID 갱신을 동시에 처리
                                    setMessages(prev =>
                                        prev.map(msg => {
                                            if (msg.id !== aiMessageId) return msg;
                                            const updated: ChatMessageData = {
                                                ...msg,
                                                content: streamingContentRef.current,
                                                isStreaming: false,
                                            };
                                            if (parsed.message_id) {
                                                (updated as any).id = parsed.message_id;
                                            }
                                            return updated;
                                        })
                                    );

                                    // ref 초기화 (렌더 후)
                                    streamingMessageIdRef.current = null;
                                    streamingContentRef.current = '';

                                    setIsSendingMessage(false);

                                    // 첫 메시지인 경우 응답 내용으로 세션 제목 업데이트
                                    if (currentSessionId && messages.length === 1) {
                                        const aiMessage = messages.find(msg => msg.id === aiMessageId);
                                        if (aiMessage && aiMessage.content) {
                                            const summary = aiMessage.content.length > 50
                                                ? aiMessage.content.substring(0, 50) + '...'
                                                : aiMessage.content;
                                            updateSessionTitleFromMessage(currentSessionId, summary);
                                        }
                                    }
                                    return;
                                } else if (parsed.type === 'error') {
                                    console.error('스트리밍 에러:', parsed.error);
                                    setMessages(prev => prev.filter(msg => msg.id !== aiMessageId));

                                    const errorMessage: ChatMessageData = {
                                        id: `error-${Date.now()}`,
                                        content: `죄송합니다. 오류가 발생했습니다: ${parsed.error}`,
                                        isUser: false,
                                        timestamp: new Date(),
                                    };

                                    setMessages(prev => [...prev, errorMessage]);
                                    setIsSendingMessage(false);
                                    return;
                                }
                            } catch (parseError) {
                                console.error('JSON 파싱 오류:', parseError, '데이터:', data);
                            }
                        }
                    }
                }
            } catch (streamError: any) {
                // AbortError 등 정상 취소는 무시
                if (streamError?.name === 'AbortError') {
                    console.warn('스트림이 취소되었습니다(Abort).');
                } else {
                    console.error('스트림 읽기 오류:', streamError);
                    // 기존 AI 메시지를 삭제하지 말고, 상태만 종료시키고 에러 알림 추가
                    setMessages(prev =>
                        prev.map(msg =>
                            msg.id === aiMessageId
                                ? { ...msg, isStreaming: false }
                                : msg
                        )
                    );

                    const errorMessage: ChatMessageData = {
                        id: `error-${Date.now()}`,
                        content: '스트림 읽기 중 오류가 발생했습니다.',
                        isUser: false,
                        timestamp: new Date(),
                    };

                    setMessages(prev => [...prev, errorMessage]);
                }
            } finally {
                reader.releaseLock();
                setIsSendingMessage(false);
                setIsLoading(false);
            }
        } catch (error) {
            // AbortError 등 정상 취소는 무시
            if ((error as any)?.name === 'AbortError') {
                console.warn('요청이 취소되었습니다(Abort).');
            } else {
                console.error('메시지 전송 실패:', error);

                // 기존 AI 메시지를 삭제하지 않음. 에러만 추가
                const errorMessage: ChatMessageData = {
                    id: `error-${Date.now()}`,
                    content: `메시지 전송에 실패했습니다: ${error instanceof Error ? error.message : '알 수 없는 오류'}`,
                    isUser: false,
                    timestamp: new Date(),
                };

                setMessages(prev => [...prev, errorMessage]);
            }
            setIsSendingMessage(false);
            setIsLoading(false);
        }
    }, [currentSessionId, isSendingMessage, updateStreamingContent, updateSessionTitleFromMessage, messages.length]);

    return (
        <div className="flex flex-col h-full">
            <ChatList messages={messages} isLoading={isLoading} />
            <ChatInput onSendMessage={handleSendMessage} disabled={isSendingMessage} />
        </div>
    );
}
