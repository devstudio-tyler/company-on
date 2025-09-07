"""
문서 관련 데이터베이스 모델
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, BigInteger, Boolean, Index, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from ..database.connection import Base


class Document(Base):
    """
    문서 모델 (모든 사용자가 공유)
    """
    __tablename__ = "documents"
    
    id = Column(BigInteger, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)  # MinIO 경로
    file_size = Column(BigInteger, nullable=False)
    content_type = Column(String(100), nullable=False)
    status = Column(String(20), default='processing')  # 'processing'|'completed'|'failed'
    document_metadata = Column(JSONB, nullable=True)  # JSON 형태로 저장
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 관계 설정
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    
    # 인덱스 설정
    __table_args__ = (
        Index('idx_documents_status', 'status'),
        Index('idx_documents_created', 'created_at'),
    )


class DocumentChunk(Base):
    """
    문서 청크 모델 (문서를 작은 조각으로 나눈 것)
    """
    __tablename__ = "document_chunks"
    
    id = Column(BigInteger, primary_key=True, index=True)
    document_id = Column(BigInteger, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)  # 청크 순서
    content = Column(Text, nullable=False)
    embedding = Column(Vector(768), nullable=False)
    chunk_metadata = Column(JSONB, nullable=True)  # JSON 형태로 저장 (페이지 번호 등)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 관계 설정
    document = relationship("Document", back_populates="chunks")
    
    # 인덱스 설정
    __table_args__ = (
        Index('idx_document_chunks_document_index', 'document_id', 'chunk_index'),
        Index('idx_document_chunks_embedding_hnsw', 'embedding', postgresql_using='hnsw',
              postgresql_with={'m': 16, 'ef_construction': 64}),
    )


class EmbeddingCache(Base):
    """
    임베딩 캐시 모델 (중복 임베딩 방지)
    """
    __tablename__ = "embedding_cache"
    
    id = Column(BigInteger, primary_key=True, index=True)
    content_hash = Column(String(64), unique=True, nullable=False, index=True)
    embedding = Column(Vector(768), nullable=False)
    model_name = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 인덱스 설정
    __table_args__ = (
        Index('idx_embedding_cache_hash', 'content_hash'),
        Index('idx_embedding_cache_model', 'model_name'),
    )
