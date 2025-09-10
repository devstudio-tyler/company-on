// 세션 관련 API 클라이언트

import { getClientId } from '@/lib/utils';

export interface ChatSession {
    id: string;
    title: string;
    description?: string;
    client_id: string;
    created_at: string;
    updated_at: string;
    message_count: number;
    is_pinned?: boolean;
    tags?: string[];
}

export interface ChatSessionCreateRequest {
    title: string;
    description?: string;
    tags?: string[];
}

export interface ChatSessionUpdateRequest {
    title?: string;
    description?: string;
    tags?: string[];
}

export interface ChatSessionListResponse {
    sessions: ChatSession[];
    total: number;
    page: number;
    size: number;
}

export interface ChatMessage {
    id: string;
    content: string;
    is_user: boolean;
    session_id: string;
    client_id: string;
    sources?: any[];
    usage?: any;
    model?: string;
    created_at: string;
}

export interface ChatMessageListResponse {
    messages: ChatMessage[];
    total: number;
    page: number;
    size: number;
}

const API_BASE = '/api/v1';

// 세션 목록 조회
export async function getSessions(
    clientId: string,
    page: number = 1,
    size: number = 20
): Promise<ChatSessionListResponse> {
    const url = `${API_BASE}/chat/sessions?page=${page}&size=${size}`;
    console.log('🔍 세션 조회 요청:', { url, clientId, page, size });

    try {
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-Client-ID': clientId,
            },
        });

        console.log('📡 세션 조회 응답:', {
            status: response.status,
            statusText: response.statusText,
            ok: response.ok,
            url: response.url
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.error('❌ 세션 조회 실패:', {
                status: response.status,
                statusText: response.statusText,
                errorText
            });
            throw new Error(`세션 목록 조회 실패: ${response.status}`);
        }

        const data = await response.json();
        console.log('✅ 세션 조회 성공:', data);

        // 백엔드 응답에서 session_id를 id로 매핑
        return {
            ...data,
            sessions: data.sessions.map((session: any) => ({
                ...session,
                id: session.session_id
            }))
        };
    } catch (error) {
        console.error('💥 세션 조회 에러:', error);
        throw error;
    }
}

// 새 세션 생성
export async function createSession(
    clientId: string,
    request: ChatSessionCreateRequest
): Promise<ChatSession> {
    const response = await fetch(`${API_BASE}/chat/sessions`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Client-ID': clientId,
        },
        body: JSON.stringify(request),
    });

    if (!response.ok) {
        throw new Error(`세션 생성 실패: ${response.status}`);
    }

    const data = await response.json();
    // 백엔드 응답에서 session_id를 id로 매핑
    return {
        ...data,
        id: data.session_id
    };
}

// 세션 삭제
export async function deleteSession(sessionId: string, clientId: string): Promise<void> {
    const response = await fetch(`${API_BASE}/chat/sessions/${sessionId}`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json',
            'X-Client-ID': clientId,
        },
    });

    if (!response.ok) {
        throw new Error(`세션 삭제 실패: ${response.status}`);
    }
}

// 세션별 메시지 조회
export async function getSessionMessages(
    sessionId: string,
    page: number = 1,
    size: number = 50
): Promise<ChatMessageListResponse> {
    const clientId = getClientId();

    const response = await fetch(
        `${API_BASE}/chat/sessions/${sessionId}/messages?page=${page}&size=${size}`,
        {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-Client-ID': clientId,
            },
        }
    );

    if (!response.ok) {
        throw new Error(`메시지 조회 실패: ${response.status}`);
    }

    const data = await response.json();
    // 백엔드의 message_id를 프론트 타입의 id로 매핑
    return {
        ...data,
        messages: (data.messages || []).map((m: any) => ({
            ...m,
            id: m.id ?? m.message_id
        }))
    };
}

// 메시지 피드백 업데이트
export async function updateMessageFeedback(
    messageId: string,
    feedback: 'up' | 'down' | 'none',
    comment?: string
): Promise<{ message_id: string; feedback: string; comment?: string; created_at: string }> {
    const clientId = getClientId();
    const response = await fetch(`${API_BASE}/chat/messages/${messageId}/feedback`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Client-ID': clientId,
        },
        body: JSON.stringify({ message_id: messageId, feedback, comment }),
    });
    if (!response.ok) {
        const text = await response.text();
        throw new Error(`피드백 업데이트 실패: ${response.status} ${text}`);
    }
    return response.json();
}

// 피드백 통계 (전체: 클라이언트 기준)
export async function getFeedbackStatsOverall(): Promise<{ total: number; up: number; down: number; none: number; rate_up: number; rate_down: number }> {
    const clientId = getClientId();
    const response = await fetch(`${API_BASE}/chat/feedback/stats`, {
        headers: {
            'X-Client-ID': clientId,
        },
    });
    if (!response.ok) throw new Error(`피드백 통계 조회 실패: ${response.status}`);
    return response.json();
}

// 피드백 통계 (세션별)
export async function getFeedbackStatsBySession(sessionId: string): Promise<{ total: number; up: number; down: number; none: number; rate_up: number; rate_down: number }> {
    const clientId = getClientId();
    const response = await fetch(`${API_BASE}/chat/sessions/${sessionId}/feedback/stats`, {
        headers: {
            'X-Client-ID': clientId,
        },
    });
    if (!response.ok) throw new Error(`세션 피드백 통계 조회 실패: ${response.status}`);
    return response.json();
}

// 세션 업데이트 (모든 필드 통합)
export async function updateSession(
    sessionId: string,
    title: string,
    description: string,
    tags: string[],
    isPinned: boolean,
    clientId: string
): Promise<ChatSession> {
    const response = await fetch(`${API_BASE}/chat/sessions/${sessionId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'X-Client-ID': clientId,
        },
        body: JSON.stringify({
            title,
            description,
            tags,
            is_pinned: isPinned
        }),
    });

    if (!response.ok) {
        throw new Error(`세션 업데이트 실패: ${response.status}`);
    }

    const data = await response.json();
    // 백엔드 응답에서 session_id를 id로 매핑
    return {
        ...data,
        id: data.session_id
    };
}

// 세션 제목 업데이트 (하위 호환성을 위해 유지)
export async function updateSessionTitle(
    sessionId: string,
    title: string,
    clientId: string
): Promise<ChatSession> {
    return updateSession(sessionId, title, '', [], false, clientId);
}

// 세션 고정 상태 업데이트
export async function updateSessionPin(
    sessionId: string,
    isPinned: boolean,
    clientId: string
): Promise<ChatSession> {
    const response = await fetch(`${API_BASE}/chat/sessions/${sessionId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'X-Client-ID': clientId,
        },
        body: JSON.stringify({ is_pinned: isPinned }),
    });

    if (!response.ok) {
        throw new Error(`세션 고정 상태 업데이트 실패: ${response.status}`);
    }

    const data = await response.json();
    // 백엔드 응답에서 session_id를 id로 매핑
    return {
        ...data,
        id: data.session_id
    };
}

// 새 세션 생성 (자동 제목)
export async function createNewSession(clientId: string, title?: string): Promise<ChatSession> {
    const now = new Date();
    const sessionTitle = title || `새 대화 ${now.toLocaleDateString('ko-KR')} ${now.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })}`;

    return createSession(clientId, { title: sessionTitle });
}
