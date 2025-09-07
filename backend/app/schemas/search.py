"""
검색 관련 Pydantic 스키마
하이브리드 검색, 문서 검색, 채팅 세션 검색을 위한 요청/응답 스키마
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class SearchRequest(BaseModel):
    """하이브리드 검색 요청"""
    query: str = Field(..., description="검색 쿼리", min_length=1, max_length=500)
    limit: int = Field(10, description="반환할 결과 수", ge=1, le=100)
    alpha: float = Field(0.7, description="Dense 검색 가중치", ge=0.0, le=1.0)
    beta: float = Field(0.3, description="BM25 검색 가중치", ge=0.0, le=1.0)
    
    class Config:
        schema_extra = {
            "example": {
                "query": "회사 정책 문서",
                "limit": 10,
                "alpha": 0.7,
                "beta": 0.3
            }
        }


class SearchResult(BaseModel):
    """검색 결과 항목"""
    id: int = Field(..., description="청크 ID")
    document_id: int = Field(..., description="문서 ID")
    chunk_text: str = Field(..., description="청크 텍스트")
    chunk_metadata: Optional[Dict[str, Any]] = Field(None, description="청크 메타데이터")
    filename: str = Field(..., description="파일명")
    document_metadata: Optional[Dict[str, Any]] = Field(None, description="문서 메타데이터")
    bm25_score: float = Field(..., description="BM25 점수")
    dense_score: float = Field(..., description="Dense 점수")
    combined_score: float = Field(..., description="통합 점수")


class SearchResponse(BaseModel):
    """하이브리드 검색 응답"""
    query: str = Field(..., description="검색 쿼리")
    total_results: int = Field(..., description="총 결과 수")
    results: List[SearchResult] = Field(..., description="검색 결과")
    search_type: str = Field("hybrid", description="검색 타입")


class DocumentSearchRequest(BaseModel):
    """문서 검색 요청"""
    query: str = Field(..., description="검색 쿼리", min_length=1, max_length=500)
    document_ids: Optional[List[int]] = Field(None, description="검색할 문서 ID 리스트")
    limit: int = Field(10, description="반환할 결과 수", ge=1, le=100)
    
    class Config:
        schema_extra = {
            "example": {
                "query": "회사 정책",
                "document_ids": [1, 2, 3],
                "limit": 10
            }
        }


class DocumentSearchResponse(BaseModel):
    """문서 검색 응답"""
    query: str = Field(..., description="검색 쿼리")
    document_ids: Optional[List[int]] = Field(None, description="검색한 문서 ID 리스트")
    total_results: int = Field(..., description="총 결과 수")
    results: List[SearchResult] = Field(..., description="검색 결과")


class ChatSearchRequest(BaseModel):
    """채팅 세션 검색 요청"""
    query: str = Field(..., description="검색 쿼리", min_length=1, max_length=500)
    client_id: str = Field(..., description="클라이언트 ID")
    limit: int = Field(10, description="반환할 결과 수", ge=1, le=100)
    
    class Config:
        schema_extra = {
            "example": {
                "query": "회의록",
                "client_id": "550e8400-e29b-41d4-a716-446655440000",
                "limit": 10
            }
        }


class ChatSearchResult(BaseModel):
    """채팅 세션 검색 결과"""
    id: int = Field(..., description="세션 ID")
    summary: Optional[str] = Field(None, description="세션 요약")
    tags: Optional[Dict[str, Any]] = Field(None, description="세션 태그")
    created_at: datetime = Field(..., description="생성일시")
    similarity_score: float = Field(..., description="유사도 점수")


class ChatSearchResponse(BaseModel):
    """채팅 세션 검색 응답"""
    query: str = Field(..., description="검색 쿼리")
    client_id: str = Field(..., description="클라이언트 ID")
    total_results: int = Field(..., description="총 결과 수")
    results: List[ChatSearchResult] = Field(..., description="검색 결과")


class SearchStatisticsResponse(BaseModel):
    """검색 통계 응답"""
    total_documents: int = Field(..., description="전체 문서 수")
    total_chunks: int = Field(..., description="전체 청크 수")
    chunks_with_embeddings: int = Field(..., description="임베딩이 있는 청크 수")
    embedding_coverage: float = Field(..., description="임베딩 커버리지 비율")
    total_sessions: int = Field(..., description="전체 채팅 세션 수")


class SearchTestResponse(BaseModel):
    """검색 테스트 응답"""
    message: str = Field(..., description="테스트 결과 메시지")
    query: str = Field(..., description="검색 쿼리")
    total_results: int = Field(..., description="총 결과 수")
    results: List[SearchResult] = Field(..., description="검색 결과 (최대 3개)")


class ErrorResponse(BaseModel):
    """에러 응답"""
    detail: str = Field(..., description="에러 메시지")
    error_code: Optional[str] = Field(None, description="에러 코드")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="에러 발생 시간")
