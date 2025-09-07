"""
검색 API 엔드포인트
하이브리드 검색, 문서 검색, 채팅 세션 검색 기능 제공
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from ....database.connection import get_db
from ....services.search_service import SearchService
from ....schemas.search import (
    SearchRequest, SearchResponse, DocumentSearchRequest, 
    DocumentSearchResponse, ChatSearchRequest, ChatSearchResponse,
    SearchStatisticsResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["search"])


@router.post("/hybrid", response_model=SearchResponse)
async def hybrid_search(
    request: SearchRequest,
    db: Session = Depends(get_db)
):
    """
    하이브리드 검색 (BM25 + Dense)
    
    BM25 키워드 검색과 Dense 벡터 검색을 결합한 하이브리드 검색을 수행합니다.
    """
    try:
        search_service = SearchService(db)
        
        results = search_service.hybrid_search(
            query=request.query,
            limit=request.limit,
            alpha=request.alpha,
            beta=request.beta
        )
        
        return SearchResponse(
            query=request.query,
            total_results=len(results),
            results=results,
            search_type="hybrid"
        )
        
    except Exception as e:
        logger.error(f"하이브리드 검색 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"검색 실패: {str(e)}"
        )


@router.post("/documents", response_model=DocumentSearchResponse)
async def search_documents(
    request: DocumentSearchRequest,
    db: Session = Depends(get_db)
):
    """
    문서 검색
    
    특정 문서들에서 하이브리드 검색을 수행합니다.
    """
    try:
        search_service = SearchService(db)
        
        results = search_service.search_documents(
            query=request.query,
            document_ids=request.document_ids,
            limit=request.limit
        )
        
        return DocumentSearchResponse(
            query=request.query,
            document_ids=request.document_ids,
            total_results=len(results),
            results=results
        )
        
    except Exception as e:
        logger.error(f"문서 검색 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"문서 검색 실패: {str(e)}"
        )


@router.post("/chat-sessions", response_model=ChatSearchResponse)
async def search_chat_sessions(
    request: ChatSearchRequest,
    db: Session = Depends(get_db)
):
    """
    채팅 세션 검색
    
    특정 클라이언트의 채팅 세션에서 벡터 유사도 검색을 수행합니다.
    """
    try:
        search_service = SearchService(db)
        
        results = search_service.search_chat_sessions(
            query=request.query,
            client_id=request.client_id,
            limit=request.limit
        )
        
        return ChatSearchResponse(
            query=request.query,
            client_id=request.client_id,
            total_results=len(results),
            results=results
        )
        
    except Exception as e:
        logger.error(f"채팅 세션 검색 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"채팅 세션 검색 실패: {str(e)}"
        )


@router.get("/statistics", response_model=SearchStatisticsResponse)
async def get_search_statistics(
    db: Session = Depends(get_db)
):
    """
    검색 통계 조회
    
    검색 시스템의 통계 정보를 조회합니다.
    """
    try:
        search_service = SearchService(db)
        
        statistics = search_service.get_search_statistics()
        
        return SearchStatisticsResponse(**statistics)
        
    except Exception as e:
        logger.error(f"검색 통계 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"검색 통계 조회 실패: {str(e)}"
        )


@router.get("/test")
async def test_search(
    query: str = Query(..., description="테스트 검색 쿼리"),
    limit: int = Query(5, description="반환할 결과 수"),
    db: Session = Depends(get_db)
):
    """
    검색 테스트
    
    간단한 검색 테스트를 수행합니다.
    """
    try:
        search_service = SearchService(db)
        
        # 하이브리드 검색 테스트
        results = search_service.hybrid_search(
            query=query,
            limit=limit,
            alpha=0.7,
            beta=0.3
        )
        
        return {
            "message": "검색 테스트 성공",
            "query": query,
            "total_results": len(results),
            "results": results[:3]  # 처음 3개 결과만 반환
        }
        
    except Exception as e:
        logger.error(f"검색 테스트 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"검색 테스트 실패: {str(e)}"
        )
