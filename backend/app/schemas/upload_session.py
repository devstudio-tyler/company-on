"""
업로드 세션 관련 Pydantic 스키마
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


class UploadStatus(str, Enum):
    """업로드 상태"""
    INIT = "init"           # 초기화
    UPLOADING = "uploading" # 업로드 중
    PENDING = "pending"     # 처리 대기
    PROCESSING = "processing" # 처리 중
    COMPLETED = "completed" # 완료
    FAILED = "failed"      # 실패


class UploadSessionResponse(BaseModel):
    """업로드 세션 응답"""
    id: str
    filename: str
    file_size: int
    uploaded_size: int
    content_type: str
    status: UploadStatus
    document_id: Optional[int]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UploadSessionListResponse(BaseModel):
    """업로드 세션 목록 응답"""
    sessions: list[UploadSessionResponse]
    total: int = Field(..., description="전체 세션 수")
    page: int = Field(..., ge=1, description="현재 페이지")
    limit: int = Field(..., ge=1, le=100, description="페이지당 항목 수")


class UploadProgressResponse(BaseModel):
    """업로드 진행률 응답"""
    upload_id: str
    filename: str
    status: UploadStatus
    progress_percentage: float = Field(..., ge=0, le=100, description="진행률 (%)")
    uploaded_size: int
    file_size: int
    document_id: Optional[int]
    error_message: Optional[str]
    updated_at: datetime


class UploadStatusUpdateRequest(BaseModel):
    """업로드 상태 업데이트 요청"""
    status: UploadStatus
    uploaded_size: Optional[int] = None
    document_id: Optional[int] = None
    error_message: Optional[str] = None
