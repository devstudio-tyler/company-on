"""
하이브리드 검색 서비스
BM25 (키워드 기반) + Dense (벡터 기반) 검색을 결합한 하이브리드 검색 시스템
"""
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import logging
from sqlalchemy.orm import Session
from sqlalchemy import text, func
import math

from .embedding_service import EmbeddingService
from ..models.document import Document, DocumentChunk
from ..models.chat import ChatSession, ChatMessage

logger = logging.getLogger(__name__)


class SearchService:
    """하이브리드 검색 서비스"""
    
    def __init__(self, db: Session):
        self.db = db
        # 임시로 임베딩 서비스 비활성화 (SSL 오류 해결 후 재활성화)
        self.embedding_service = None
        
    def _preprocess_query(self, query: str) -> str:
        """
        검색 쿼리 전처리 (한국어 키워드 추출)
        """
        # 한국어에서 중요한 키워드들 추출
        import re
        
        # 확장된 불용어 제거
        stop_words = [
            '이', '가', '을', '를', '에', '의', '은', '는', '과', '와', '이다', '입니다', 
            '무엇', '무엇인지', '어떻게', '왜', '설명', '설명해주세요', '해주세요', '알려주세요',
            '알려', '해', '주세요', '대해', '대한', '관련', '있는', '없는', '그', '저', '이것',
            '그것', '것', '뭐', '뭔지'
        ]
        
        # 단어 분리 및 필터링
        words = re.findall(r'[가-힣a-zA-Z0-9]+', query)
        keywords = [word for word in words if len(word) > 1 and word not in stop_words]
        
        # 로그 추가
        logger.info(f"추출된 키워드: {keywords}")
        
        # 주요 키워드만 반환 (최대 5개)
        return ' '.join(keywords[:5]) if keywords else query

    def hybrid_search(
        self, 
        query: str, 
        limit: int = 10,
        alpha: float = 0.7,  # Dense 검색 가중치
        beta: float = 0.3    # BM25 검색 가중치
    ) -> List[Dict[str, Any]]:
        """
        하이브리드 검색 수행 (BM25 + Dense)
        
        Args:
            query: 검색 쿼리
            limit: 반환할 결과 수
            alpha: Dense 검색 가중치 (0.0 ~ 1.0)
            beta: BM25 검색 가중치 (0.0 ~ 1.0)
            
        Returns:
            검색 결과 리스트
        """
        try:
            # 쿼리 전처리
            processed_query = self._preprocess_query(query)
            logger.info(f"원본 쿼리: '{query}' -> 처리된 쿼리: '{processed_query}'")
            
            # 1. BM25 검색 수행
            bm25_results = self._bm25_search(processed_query, limit * 2)  # 더 많은 결과를 가져와서 후보 확보
            
            # 2. Dense 검색 수행 (원본 쿼리 사용 - 의미적 유사성을 위해)
            dense_results = self._dense_search(query, limit * 2)
            
            # 3. 결과 통합 및 점수 계산
            combined_results = self._combine_results(
                bm25_results, dense_results, alpha, beta
            )
            
            # 4. 상위 결과 반환
            return combined_results[:limit]
            
        except Exception as e:
            logger.error(f"하이브리드 검색 실패: {str(e)}")
            raise
    
    def _bm25_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """
        BM25 키워드 기반 검색
        
        Args:
            query: 검색 쿼리
            limit: 반환할 결과 수
            
        Returns:
            BM25 검색 결과
        """
        try:
            # PostgreSQL의 full-text search 사용 (한국어 지원 개선)
            
            sql_query = text("""
                SELECT 
                    dc.id,
                    dc.document_id,
                    dc.content,
                    dc.chunk_metadata,
                    d.filename,
                    d.document_metadata,
                    CASE 
                        WHEN dc.content ILIKE :ilike_query THEN 1.0
                        WHEN to_tsvector('simple', dc.content) @@ plainto_tsquery('simple', :query) THEN 0.8
                        ELSE 0.5
                    END as bm25_score
                FROM document_chunks dc
                JOIN documents d ON dc.document_id = d.id
                WHERE dc.content ILIKE :ilike_query 
                   OR to_tsvector('simple', dc.content) @@ plainto_tsquery('simple', :query)
                ORDER BY bm25_score DESC
                LIMIT :limit
            """)
            
            # 키워드 추출 및 ILIKE 패턴 생성 (더 유연한 패턴)
            keywords = query.split()
            # 각 키워드를 개별적으로 검색할 수 있도록 패턴 생성
            main_keywords = [kw for kw in keywords if len(kw) > 1]
            
            if main_keywords:
                # 가장 중요한 키워드들로 OR 조건 생성
                ilike_query = f'%{main_keywords[0]}%'
            else:
                ilike_query = f'%{query}%'
            
            logger.info(f"BM25 검색 - 쿼리: '{query}', ILIKE 패턴: '{ilike_query}'")
            
            results = self.db.execute(sql_query, {
                "query": query, 
                "ilike_query": ilike_query,
                "limit": limit
            }).fetchall()
            
            logger.info(f"BM25 검색 결과 수: {len(results)}")
            
            return [
                {
                    "id": row.id,
                    "document_id": row.document_id,
                    "chunk_text": row.content,
                    "chunk_metadata": row.chunk_metadata,
                    "filename": row.filename,
                    "document_metadata": row.document_metadata,
                    "bm25_score": float(row.bm25_score),
                    "dense_score": 0.0,  # 나중에 업데이트
                    "combined_score": 0.0  # 나중에 업데이트
                }
                for row in results
            ]
            
        except Exception as e:
            logger.error(f"BM25 검색 실패: {str(e)}")
            return []
    
    def _dense_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """
        Dense 벡터 기반 검색
        
        Args:
            query: 검색 쿼리
            limit: 반환할 결과 수
            
        Returns:
            Dense 검색 결과
        """
        try:
            # 임베딩 서비스가 비활성화된 경우 빈 결과 반환
            if self.embedding_service is None:
                return []
                
            # 쿼리 임베딩 생성
            query_embedding = self.embedding_service.generate_embedding(query)
            
            # 벡터 유사도 검색 (코사인 유사도)
            sql_query = text("""
                SELECT 
                    dc.id,
                    dc.document_id,
                    dc.content,
                    dc.chunk_metadata,
                    d.filename,
                    d.document_metadata,
                    1 - (dc.embedding <=> :query_embedding) as dense_score
                FROM document_chunks dc
                JOIN documents d ON dc.document_id = d.id
                WHERE dc.embedding IS NOT NULL
                ORDER BY dc.embedding <=> :query_embedding
                LIMIT :limit
            """)
            
            results = self.db.execute(
                sql_query, 
                {
                    "query_embedding": query_embedding.tolist(),
                    "limit": limit
                }
            ).fetchall()
            
            return [
                {
                    "id": row.id,
                    "document_id": row.document_id,
                    "chunk_text": row.content,
                    "chunk_metadata": row.chunk_metadata,
                    "filename": row.filename,
                    "document_metadata": row.document_metadata,
                    "bm25_score": 0.0,  # 나중에 업데이트
                    "dense_score": float(row.dense_score),
                    "combined_score": 0.0  # 나중에 업데이트
                }
                for row in results
            ]
            
        except Exception as e:
            logger.error(f"Dense 검색 실패: {str(e)}")
            return []
    
    def _combine_results(
        self, 
        bm25_results: List[Dict[str, Any]], 
        dense_results: List[Dict[str, Any]], 
        alpha: float, 
        beta: float
    ) -> List[Dict[str, Any]]:
        """
        BM25와 Dense 검색 결과를 통합
        
        Args:
            bm25_results: BM25 검색 결과
            dense_results: Dense 검색 결과
            alpha: Dense 검색 가중치
            beta: BM25 검색 가중치
            
        Returns:
            통합된 검색 결과
        """
        # 결과를 딕셔너리로 변환 (chunk_id를 키로 사용)
        combined_dict = {}
        
        # BM25 결과 추가
        for result in bm25_results:
            chunk_id = result["id"]
            combined_dict[chunk_id] = result.copy()
        
        # Dense 결과 추가/업데이트
        for result in dense_results:
            chunk_id = result["id"]
            if chunk_id in combined_dict:
                # 기존 결과에 Dense 점수 추가
                combined_dict[chunk_id]["dense_score"] = result["dense_score"]
            else:
                # 새로운 결과 추가
                combined_dict[chunk_id] = result.copy()
        
        # 점수 정규화 및 통합 점수 계산
        bm25_scores = [r["bm25_score"] for r in combined_dict.values() if r["bm25_score"] > 0]
        dense_scores = [r["dense_score"] for r in combined_dict.values() if r["dense_score"] > 0]
        
        # Min-Max 정규화
        bm25_min, bm25_max = (min(bm25_scores), max(bm25_scores)) if bm25_scores else (0, 1)
        dense_min, dense_max = (min(dense_scores), max(dense_scores)) if dense_scores else (0, 1)
        
        for result in combined_dict.values():
            # 점수 정규화
            if bm25_max > bm25_min:
                normalized_bm25 = (result["bm25_score"] - bm25_min) / (bm25_max - bm25_min)
            else:
                normalized_bm25 = result["bm25_score"]
                
            if dense_max > dense_min:
                normalized_dense = (result["dense_score"] - dense_min) / (dense_max - dense_min)
            else:
                normalized_dense = result["dense_score"]
            
            # 통합 점수 계산
            result["combined_score"] = alpha * normalized_dense + beta * normalized_bm25
        
        # 통합 점수로 정렬
        return sorted(
            combined_dict.values(), 
            key=lambda x: x["combined_score"], 
            reverse=True
        )
    
    def search_documents(
        self, 
        query: str, 
        document_ids: Optional[List[int]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        특정 문서들에서 검색
        
        Args:
            query: 검색 쿼리
            document_ids: 검색할 문서 ID 리스트 (None이면 모든 문서)
            limit: 반환할 결과 수
            
        Returns:
            검색 결과 리스트
        """
        try:
            # 기본 하이브리드 검색 수행
            results = self.hybrid_search(query, limit)
            
            # 문서 ID 필터링
            if document_ids:
                results = [r for r in results if r["document_id"] in document_ids]
            
            return results
            
        except Exception as e:
            logger.error(f"문서 검색 실패: {str(e)}")
            raise
    
    def search_chat_sessions(
        self, 
        query: str, 
        client_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        채팅 세션에서 검색
        
        Args:
            query: 검색 쿼리
            client_id: 클라이언트 ID
            limit: 반환할 결과 수
            
        Returns:
            검색 결과 리스트
        """
        try:
            # 채팅 세션 임베딩 검색
            query_embedding = self.embedding_service.generate_embedding(query)
            
            sql_query = text("""
                SELECT 
                    cs.id,
                    cs.summary,
                    cs.tags,
                    cs.created_at,
                    1 - (cse.embedding <=> :query_embedding) as similarity_score
                FROM chat_sessions cs
                LEFT JOIN chat_session_embeddings cse ON cs.id = cse.session_id
                WHERE cs.client_id = :client_id
                AND cse.embedding IS NOT NULL
                ORDER BY cse.embedding <=> :query_embedding
                LIMIT :limit
            """)
            
            results = self.db.execute(
                sql_query,
                {
                    "query_embedding": query_embedding.tolist(),
                    "client_id": client_id,
                    "limit": limit
                }
            ).fetchall()
            
            return [
                {
                    "id": row.id,
                    "summary": row.summary,
                    "tags": row.tags,
                    "created_at": row.created_at,
                    "similarity_score": float(row.similarity_score)
                }
                for row in results
            ]
            
        except Exception as e:
            logger.error(f"채팅 세션 검색 실패: {str(e)}")
            raise
    
    def get_search_statistics(self) -> Dict[str, Any]:
        """
        검색 통계 조회
        
        Returns:
            검색 통계 정보
        """
        try:
            # 전체 문서 수
            total_documents = self.db.query(Document).count()
            
            # 전체 청크 수
            total_chunks = self.db.query(DocumentChunk).count()
            
            # 임베딩이 있는 청크 수
            chunks_with_embeddings = self.db.query(DocumentChunk).filter(
                DocumentChunk.embedding.isnot(None)
            ).count()
            
            # 전체 채팅 세션 수
            total_sessions = self.db.query(ChatSession).count()
            
            return {
                "total_documents": total_documents,
                "total_chunks": total_chunks,
                "chunks_with_embeddings": chunks_with_embeddings,
                "embedding_coverage": chunks_with_embeddings / total_chunks if total_chunks > 0 else 0,
                "total_sessions": total_sessions
            }
            
        except Exception as e:
            logger.error(f"검색 통계 조회 실패: {str(e)}")
            raise


# 전역 인스턴스는 의존성 주입으로 생성
def get_search_service(db: Session) -> SearchService:
    """SearchService 인스턴스 생성"""
    return SearchService(db)
