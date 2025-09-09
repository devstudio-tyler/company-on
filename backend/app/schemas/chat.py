"""
채팅 관련 스키마
"""

from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ChatMessageRole(str, Enum):
    """채팅 메시지 역할"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class FeedbackType(str, Enum):
    """피드백 타입"""
    UP = "up"
    DOWN = "down"
    NONE = "none"


class ChatMessageRequest(BaseModel):
    """채팅 메시지 요청"""
    content: str
    client_id: str
    session_id: Optional[str] = None
    max_results: int = 5
    include_history: bool = True


class ChatMessageCreateRequest(BaseModel):
    """채팅 메시지 생성 요청 (기존 호환성)"""
    content: str
    session_id: str
    client_id: str
    is_user: bool = True


class ChatMessageResponse(BaseModel):
    """채팅 메시지 응답"""
    message_id: str
    content: str
    is_user: bool
    session_id: str
    client_id: str
    sources: List[Dict[str, Any]]
    usage: Dict[str, int]
    model: str
    created_at: datetime


class ChatSessionRequest(BaseModel):
    """채팅 세션 생성 요청"""
    client_id: str
    title: Optional[str] = None


class ChatSessionCreateRequest(BaseModel):
    """채팅 세션 생성 요청"""
    title: str
    description: Optional[str] = None
    tags: Optional[List[str]] = None


class ChatSessionUpdateRequest(BaseModel):
    """채팅 세션 업데이트 요청"""
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    is_pinned: Optional[bool] = None


class ChatSessionSearchRequest(BaseModel):
    """채팅 세션 검색 요청"""
    query: Optional[str] = None
    client_id: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = None
    page: int = 1
    size: int = 20


class ChatSessionStatus(str, Enum):
    """채팅 세션 상태"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class ChatSessionResponse(BaseModel):
    """채팅 세션 응답"""
    session_id: str
    client_id: str
    title: str
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    is_pinned: Optional[bool] = False
    created_at: datetime
    updated_at: datetime
    message_count: int


class ChatSessionListResponse(BaseModel):
    """채팅 세션 목록 응답"""
    sessions: List[ChatSessionResponse]
    total: int
    page: int
    size: int


class ChatMessageListResponse(BaseModel):
    """채팅 메시지 목록 응답"""
    messages: List[ChatMessageResponse]
    total: int
    page: int
    size: int


class ChatMessageFeedbackRequest(BaseModel):
    """채팅 메시지 피드백 요청"""
    message_id: str
    feedback: FeedbackType
    comment: Optional[str] = None


class ChatMessageFeedbackResponse(BaseModel):
    """채팅 메시지 피드백 응답"""
    message_id: str
    feedback: FeedbackType
    comment: Optional[str] = None
    created_at: datetime


class RAGTestResponse(BaseModel):
    """RAG 테스트 응답"""
    search_working: bool
    llm_connected: bool
    search_results_count: int
    test_query: str
    error: Optional[str] = None


class ErrorResponse(BaseModel):
    """에러 응답"""
    error: str
    detail: Optional[str] = None
    status_code: int