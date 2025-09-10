'use client';

import { getSessionMessages, updateMessageFeedback, updateSessionTitle, type ChatMessage } from '@/lib/api/sessions';
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

    // 세션 메시지를 ChatMessageData 형식으로 변환
    const convertSessionMessagesToChatData = useCallback((messages: ChatMessage[]): ChatMessageData[] => {
        return messages.map(msg => ({
            id: `session-${msg.id}`, // API 매핑 후 통일된 id 사용
            content: msg.content,
            isUser: msg.is_user,
            timestamp: new Date(msg.created_at),
            sources: msg.sources || []
        }));
    }, []);

    // 세션 메시지 로드
    const loadSessionMessages = useCallback(async (sessionId: string) => {
        try {
            setIsLoading(true);
            console.log('📥 세션 메시지 로딩 시작:', sessionId);

            const response = await getSessionMessages(sessionId);
            const chatMessages = convertSessionMessagesToChatData(response.messages);

            console.log('✅ 세션 메시지 로드 완료:', {
                sessionId,
                messageCount: chatMessages.length,
                messages: chatMessages
            });

            setMessages(chatMessages);
        } catch (error) {
            console.error('❌ 세션 메시지 로드 실패:', error);
            setMessages([]); // 실패 시 빈 배열
        } finally {
            setIsLoading(false);
        }
    }, [convertSessionMessagesToChatData]);

    // sessionId prop이 변경될 때 currentSessionId 업데이트 및 메시지 로드
    useEffect(() => {
        const newSessionId = sessionId || null;
        setCurrentSessionId(newSessionId);

        // 기존 스트리밍 취소
        if (eventSource) {
            console.log('🛑 기존 스트리밍 연결 취소 (세션 변경)');
            eventSource.close();
            setEventSource(null);
        }

        // 스트리밍 관련 상태 초기화
        setIsSendingMessage(false);
        streamingContentRef.current = '';
        streamingMessageIdRef.current = null;
        if (updateTimeoutRef.current) {
            clearTimeout(updateTimeoutRef.current);
            updateTimeoutRef.current = null;
        }

        // 새 세션이 선택된 경우 메시지 로드
        if (newSessionId) {
            loadSessionMessages(newSessionId);
        } else {
            // 세션이 없으면 메시지 초기화
            setMessages([]);
        }
    }, [sessionId, eventSource, loadSessionMessages]);

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
                                        // 첫 번째 청크에서 leading whitespace 제거
                                        const trimmedContent = parsed.content.trimStart();
                                        streamingContentRef.current = trimmedContent;
                                        // 첫 번째 청크는 즉시 업데이트
                                        setMessages(prev =>
                                            prev.map(msg =>
                                                msg.id === aiMessageId
                                                    ? { ...msg, content: trimmedContent }
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
                                    console.log('📄 최종 내용:', streamingContentRef.current);
                                    console.log('🆔 세션 정보:', {
                                        현재세션: currentSessionId,
                                        응답세션: parsed.session_id,
                                        전체응답: parsed
                                    });

                                    // 디바운싱 타이머 즉시 해제하고 최종 업데이트 실행
                                    if (updateTimeoutRef.current) {
                                        clearTimeout(updateTimeoutRef.current);
                                        updateTimeoutRef.current = null;
                                    }

                                    // 새 세션이 생성된 경우 세션 ID 업데이트
                                    if (!currentSessionId && parsed.session_id) {
                                        console.log('🆕 새 세션 생성됨:', parsed.session_id);
                                        setCurrentSessionId(parsed.session_id);

                                        // 세션 업데이트 이벤트 발생 (사이드바 갱신용)
                                        window.dispatchEvent(new CustomEvent('sessionCreated', {
                                            detail: { sessionId: parsed.session_id }
                                        }));
                                    }

                                    // 최종 메시지 상태 업데이트 - content, isStreaming, message_id 모두 한 번에 처리
                                    const finalContent = streamingContentRef.current;
                                    setMessages(prev =>
                                        prev.map(msg => {
                                            if (msg.id !== aiMessageId) return msg;

                                            console.log('🔄 메시지 업데이트:', {
                                                기존내용: msg.content,
                                                최종내용: finalContent,
                                                메시지ID: parsed.message_id
                                            });

                                            return {
                                                ...msg,
                                                id: parsed.message_id || msg.id,
                                                content: finalContent,
                                                isStreaming: false,
                                            };
                                        })
                                    );

                                    // ref 초기화
                                    streamingContentRef.current = '';
                                    streamingMessageIdRef.current = null;

                                    setIsSendingMessage(false);

                                    // 첫 메시지인 경우 응답 내용으로 세션 제목 업데이트
                                    const sessionToUpdate = currentSessionId || parsed.session_id;
                                    if (sessionToUpdate && messages.length <= 2) { // 사용자 메시지 + AI 메시지 = 2개
                                        const summary = finalContent.length > 50
                                            ? finalContent.substring(0, 50) + '...'
                                            : finalContent;

                                        console.log('📝 세션 제목 자동 업데이트:', {
                                            sessionId: sessionToUpdate,
                                            summary,
                                            messageCount: messages.length
                                        });

                                        updateSessionTitleFromMessage(sessionToUpdate, summary);
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

    // 메시지 피드백 처리
    const handleMessageFeedback = useCallback(async (messageId: string, feedback: 'up' | 'down', comment?: string) => {
        try {
            // 아직 DB에 저장되지 않은 임시 메시지(예: 'ai-')는 차단
            if (messageId.startsWith('ai-') || messageId.startsWith('user-')) {
                alert('아직 저장되지 않은 메시지입니다. 응답이 완료된 후 다시 시도해주세요.');
                return;
            }
            // 세션에서 불러온 메시지는 id에 접두사 'session-'이 있음 → 제거
            const backendId = messageId.startsWith('session-') ? messageId.replace('session-', '') : messageId;
            await updateMessageFeedback(backendId, feedback, comment);
            // 성공 시 로컬 상태 업데이트
            setMessages(prev => prev.map(m => m.id === messageId ? { ...m, feedback } : m));
        } catch (e) {
            console.error('피드백 업데이트 실패:', e);
            alert('피드백 저장에 실패했습니다. 잠시 후 다시 시도해주세요.');
        }
    }, []);

    return (
        <div className="flex flex-col h-full">
            <ChatList messages={messages} isLoading={isLoading} onFeedback={handleMessageFeedback} />
            <ChatInput onSendMessage={handleSendMessage} disabled={isSendingMessage} />
        </div>
    );
}
