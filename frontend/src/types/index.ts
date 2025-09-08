// Company-on Frontend Types

// 사용자 및 세션 관련 타입
export interface User {
    id: string;
    name: string;
    email?: string;
    avatar?: string;
}

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

export interface ChatMessage {
    id: string;
    session_id: string;
    role: 'user' | 'assistant';
    content: string;
    created_at: string;
    sources?: DocumentSource[];
    metadata?: Record<string, any>;
}

// 문서 관련 타입
export interface Document {
    id: string;
    filename: string;
    title: string;
    content_type: string;
    file_size: number;
    upload_status: 'pending' | 'processing' | 'completed' | 'failed';
    created_at: string;
    updated_at: string;
    client_id: string;
    processing_progress?: number;
    error_message?: string;
}

export interface DocumentSource {
    id: string;
    title: string;
    content: string;
    source: string;
    score: number;
    page_number?: number;
    chunk_index?: number;
}

// API 응답 타입
export interface ApiResponse<T = any> {
    success: boolean;
    data?: T;
    error?: string;
    message?: string;
}

export interface PaginatedResponse<T> extends ApiResponse<T[]> {
    pagination: {
        page: number;
        limit: number;
        total: number;
        total_pages: number;
    };
}

// 검색 관련 타입
export interface SearchRequest {
    query: string;
    session_id?: string;
    max_results?: number;
    include_history?: boolean;
}

export interface SearchResponse {
    content: string;
    sources: DocumentSource[];
    usage: {
        prompt_tokens: number;
        completion_tokens: number;
        total_tokens: number;
    };
    model: string;
    session_id?: string;
}

// 업로드 관련 타입
export interface UploadRequest {
    filename: string;
    size: number;
    content_type: string;
}

export interface UploadResponse {
    upload_id: string;
    upload_url: string;
    expires_at: string;
}

// SSE 이벤트 타입
export interface SSEEvent {
    type: 'upload_progress' | 'upload_status_change' | 'message' | 'error';
    data: any;
    timestamp: string;
}

// UI 상태 타입
export interface UIState {
    sidebarOpen: boolean;
    currentSessionId?: string;
    isLoading: boolean;
    error?: string;
}

// 폼 타입
export interface SessionFormData {
    title: string;
    description?: string;
    tags?: string[];
}

export interface MessageFormData {
    content: string;
    session_id: string;
}

// 필터 및 정렬 타입
export interface SessionFilter {
    search?: string;
    tags?: string[];
    date_range?: {
        start: string;
        end: string;
    };
    sort_by?: 'created_at' | 'updated_at' | 'title' | 'message_count';
    sort_order?: 'asc' | 'desc';
}

export interface DocumentFilter {
    search?: string;
    status?: Document['upload_status'];
    content_type?: string;
    date_range?: {
        start: string;
        end: string;
    };
    sort_by?: 'created_at' | 'updated_at' | 'filename' | 'file_size';
    sort_order?: 'asc' | 'desc';
}

