"""
업로드 세션 모델
문서 업로드 진행률 및 상태 추적
"""
from sqlalchemy import Column, String, BigInteger, DateTime, Boolean, Index
from sqlalchemy.sql import func
from ..database.connection import Base


class UploadSession(Base):
    """업로드 세션 테이블"""
    __tablename__ = "upload_sessions"
    
    id = Column(String(255), primary_key=True, index=True)  # upload_id
    filename = Column(String(255), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    uploaded_size = Column(BigInteger, default=0)
    content_type = Column(String(100), nullable=False)
    status = Column(String(20), default='init', nullable=False)  # init, uploading, pending, processing, completed, failed
    document_id = Column(BigInteger, nullable=True)  # Commit 후 연결된 문서 ID
    error_message = Column(String(500), nullable=True)  # 실패 시 에러 메시지
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_upload_sessions_status', status),
        Index('idx_upload_sessions_created', created_at.desc()),
    )
