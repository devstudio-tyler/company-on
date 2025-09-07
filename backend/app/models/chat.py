"""
채팅 관련 데이터베이스 모델
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, BigInteger, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from ..database.connection import Base


class ChatSession(Base):
    """
    채팅 세션 모델 (client_id 기반 개인화)
    """
    __tablename__ = "chat_sessions"
    
    id = Column(BigInteger, primary_key=True, index=True)
    client_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    title = Column(String(255), nullable=True)
    summary = Column(Text, nullable=True)
    tags = Column(JSONB, nullable=True)  # JSON 형태로 저장
    is_pinned = Column(String(10), default='false')  # 'true'|'false'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 관계 설정
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    embedding = relationship("ChatSessionEmbedding", back_populates="session", uselist=False, cascade="all, delete-orphan")
    
    # 인덱스 설정
    __table_args__ = (
        Index('idx_chat_sessions_client_created', 'client_id', 'created_at'),
        Index('idx_chat_sessions_tags', 'tags', postgresql_using='gin'),
    )


class ChatMessage(Base):
    """
    채팅 메시지 모델
    """
    __tablename__ = "chat_messages"
    
    id = Column(BigInteger, primary_key=True, index=True)
    session_id = Column(BigInteger, ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)  # 'user'|'assistant'|'system'
    content = Column(Text, nullable=False)
    feedback = Column(String(10), nullable=True)  # 'up'|'down'|'none'
    feedback_comment = Column(Text, nullable=True)
    parent_id = Column(BigInteger, nullable=True)  # 향후 스레딩용
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 관계 설정
    session = relationship("ChatSession", back_populates="messages")
    
    # 인덱스 설정
    __table_args__ = (
        Index('idx_chat_messages_session_role_created', 'session_id', 'role', 'created_at'),
        Index('idx_chat_messages_user_created', 'created_at', postgresql_where="role = 'user'"),
    )


class ChatSessionEmbedding(Base):
    """
    채팅 세션 임베딩 모델 (세션별 임베딩만 저장)
    """
    __tablename__ = "chat_session_embeddings"
    
    session_id = Column(BigInteger, ForeignKey("chat_sessions.id", ondelete="CASCADE"), primary_key=True)
    embedding = Column(Vector(768), nullable=False)
    model_name = Column(String(100), nullable=False, default="multilingual-e5-base")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 관계 설정
    session = relationship("ChatSession", back_populates="embedding")
    
    # 인덱스 설정 (HNSW 인덱스)
    __table_args__ = (
        Index('idx_chat_session_embeddings_hnsw', 'embedding', postgresql_using='hnsw', 
              postgresql_with={'m': 16, 'ef_construction': 64}),
    )
