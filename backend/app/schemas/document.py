"""
문서 관련 Pydantic 스키마
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class DocumentStatus(str, Enum):
    """문서 처리 상태"""
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentUploadInitRequest(BaseModel):
    """문서 업로드 시작 요청"""
    filename: str = Field(..., min_length=1, max_length=255, description="파일명")
    size: int = Field(..., gt=0, description="파일 크기 (bytes)")
    content_type: str = Field(..., description="MIME 타입")


class DocumentUploadInitResponse(BaseModel):
    """문서 업로드 시작 응답"""
    upload_id: str = Field(..., description="업로드 ID")
    upload_url: str = Field(..., description="업로드 URL")
    expires_at: datetime = Field(..., description="URL 만료 시간")


class DocumentUploadCommitRequest(BaseModel):
    """문서 업로드 완료 요청"""
    upload_id: str = Field(..., description="업로드 ID")
    metadata: Optional[Dict[str, Any]] = Field(None, description="문서 메타데이터")


class DocumentUploadCommitResponse(BaseModel):
    """문서 업로드 완료 응답"""
    document_id: int = Field(..., description="문서 ID")
    status: DocumentStatus = Field(..., description="처리 상태")


class DocumentResponse(BaseModel):
    """문서 응답"""
    id: int
    title: str
    filename: str
    file_size: int
    content_type: str
    status: DocumentStatus
    document_metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """문서 목록 응답"""
    documents: List[DocumentResponse]
    total: int = Field(..., description="전체 문서 수")
    page: int = Field(..., ge=1, description="현재 페이지")
    limit: int = Field(..., ge=1, le=100, description="페이지당 항목 수")


class DocumentReprocessRequest(BaseModel):
    """문서 재처리 요청"""
    options: Optional[Dict[str, Any]] = Field(None, description="재처리 옵션")


class DocumentReprocessResponse(BaseModel):
    """문서 재처리 응답"""
    task_id: str = Field(..., description="작업 ID")
    status: str = Field(..., description="작업 상태")


class DocumentChunkResponse(BaseModel):
    """문서 청크 응답"""
    id: int
    document_id: int
    chunk_index: int
    content: str
    chunk_metadata: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentChunkListResponse(BaseModel):
    """문서 청크 목록 응답"""
    chunks: List[DocumentChunkResponse]
    total: int = Field(..., description="전체 청크 수")


class ErrorResponse(BaseModel):
    """에러 응답"""
    error: Dict[str, Any] = Field(..., description="에러 정보")
