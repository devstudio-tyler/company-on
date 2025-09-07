from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
import uuid

class ChatSessionStatus(str, Enum):
    """채팅 세션 상태"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"

class ChatSessionCreateRequest(BaseModel):
    """채팅 세션 생성 요청"""
    title: str = Field(..., min_length=1, max_length=200, description="세션 제목")
    description: Optional[str] = Field(None, max_length=500, description="세션 설명")
    tags: Optional[List[str]] = Field(default_factory=list, description="태그 목록")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "회사 정책 문의",
                "description": "인사 정책에 대한 질문들",
                "tags": ["인사", "정책", "문의"]
            }
        }

class ChatSessionUpdateRequest(BaseModel):
    """채팅 세션 수정 요청"""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="세션 제목")
    description: Optional[str] = Field(None, max_length=500, description="세션 설명")
    tags: Optional[List[str]] = Field(None, description="태그 목록")
    status: Optional[ChatSessionStatus] = Field(None, description="세션 상태")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "회사 정책 문의 (수정됨)",
                "description": "인사 정책에 대한 질문들 - 업데이트",
                "tags": ["인사", "정책", "문의", "업데이트"],
                "status": "active"
            }
        }

class ChatSessionResponse(BaseModel):
    """채팅 세션 응답"""
    id: int = Field(..., description="세션 ID")
    client_id: str = Field(..., description="클라이언트 ID")
    title: str = Field(..., description="세션 제목")
    description: Optional[str] = Field(None, description="세션 설명")
    tags: List[str] = Field(default_factory=list, description="태그 목록")
    status: ChatSessionStatus = Field(..., description="세션 상태")
    message_count: int = Field(default=0, description="메시지 수")
    created_at: datetime = Field(..., description="생성 시간")
    updated_at: datetime = Field(..., description="수정 시간")
    last_message_at: Optional[datetime] = Field(None, description="마지막 메시지 시간")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "client_id": "550e8400-e29b-41d4-a716-446655440000",
                "title": "회사 정책 문의",
                "description": "인사 정책에 대한 질문들",
                "tags": ["인사", "정책", "문의"],
                "status": "active",
                "message_count": 5,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T11:45:00Z",
                "last_message_at": "2024-01-15T11:45:00Z"
            }
        }

class ChatSessionListResponse(BaseModel):
    """채팅 세션 목록 응답"""
    sessions: List[ChatSessionResponse] = Field(..., description="세션 목록")
    total: int = Field(..., description="전체 세션 수")
    page: int = Field(..., description="현재 페이지")
    limit: int = Field(..., description="페이지당 항목 수")
    
    class Config:
        json_schema_extra = {
            "example": {
                "sessions": [
                    {
                        "id": 1,
                        "client_id": "550e8400-e29b-41d4-a716-446655440000",
                        "title": "회사 정책 문의",
                        "description": "인사 정책에 대한 질문들",
                        "tags": ["인사", "정책", "문의"],
                        "status": "active",
                        "message_count": 5,
                        "created_at": "2024-01-15T10:30:00Z",
                        "updated_at": "2024-01-15T11:45:00Z",
                        "last_message_at": "2024-01-15T11:45:00Z"
                    }
                ],
                "total": 1,
                "page": 1,
                "limit": 20
            }
        }

class ChatSessionSearchRequest(BaseModel):
    """채팅 세션 검색 요청"""
    query: Optional[str] = Field(None, description="검색 쿼리 (제목, 설명, 태그)")
    tags: Optional[List[str]] = Field(None, description="태그 필터")
    status: Optional[ChatSessionStatus] = Field(None, description="상태 필터")
    page: int = Field(1, ge=1, description="페이지 번호")
    limit: int = Field(20, ge=1, le=100, description="페이지당 항목 수")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "정책",
                "tags": ["인사"],
                "status": "active",
                "page": 1,
                "limit": 20
            }
        }

class ChatMessageRole(str, Enum):
    """채팅 메시지 역할"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class ChatMessageCreateRequest(BaseModel):
    """채팅 메시지 생성 요청"""
    content: str = Field(..., min_length=1, max_length=10000, description="메시지 내용")
    role: ChatMessageRole = Field(..., description="메시지 역할")
    
    class Config:
        json_schema_extra = {
            "example": {
                "content": "회사 휴가 정책에 대해 알려주세요",
                "role": "user"
            }
        }

class ChatMessageResponse(BaseModel):
    """채팅 메시지 응답"""
    id: int = Field(..., description="메시지 ID")
    session_id: int = Field(..., description="세션 ID")
    content: str = Field(..., description="메시지 내용")
    role: ChatMessageRole = Field(..., description="메시지 역할")
    created_at: datetime = Field(..., description="생성 시간")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "session_id": 1,
                "content": "회사 휴가 정책에 대해 알려주세요",
                "role": "user",
                "created_at": "2024-01-15T10:30:00Z"
            }
        }

class ChatMessageListResponse(BaseModel):
    """채팅 메시지 목록 응답"""
    messages: List[ChatMessageResponse] = Field(..., description="메시지 목록")
    total: int = Field(..., description="전체 메시지 수")
    page: int = Field(..., description="현재 페이지")
    limit: int = Field(..., description="페이지당 항목 수")
    
    class Config:
        json_schema_extra = {
            "example": {
                "messages": [
                    {
                        "id": 1,
                        "session_id": 1,
                        "content": "회사 휴가 정책에 대해 알려주세요",
                        "role": "user",
                        "created_at": "2024-01-15T10:30:00Z"
                    }
                ],
                "total": 1,
                "page": 1,
                "limit": 20
            }
        }

class ErrorResponse(BaseModel):
    """에러 응답"""
    error: str = Field(..., description="에러 메시지")
    detail: Optional[str] = Field(None, description="상세 에러 정보")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "Session not found",
                "detail": "The requested chat session does not exist"
            }
        }
