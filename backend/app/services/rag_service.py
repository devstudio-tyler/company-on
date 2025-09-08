"""
RAG 서비스 - 검색 + LLM 통합
"""

import logging
from typing import List, Dict, Optional, AsyncGenerator
from pydantic import BaseModel
from ..services.search_service import SearchService
from ..services.llm_service import llm_service
from ..models.document import DocumentChunk
from ..models.chat import ChatMessage
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class RAGRequest(BaseModel):
    """RAG 요청 모델"""
    query: str
    client_id: str
    session_id: Optional[str] = None
    max_results: int = 5
    include_history: bool = True


class RAGResponse(BaseModel):
    """RAG 응답 모델"""
    answer: str
    sources: List[Dict[str, str]]
    usage: Dict[str, int]
    model: str
    session_id: str


class RAGService:
    """RAG (Retrieval Augmented Generation) 서비스"""
    
    def __init__(self):
        self.llm_service = llm_service
        
    async def generate_answer(
        self, 
        request: RAGRequest, 
        db: Session
    ) -> RAGResponse:
        """RAG 기반 답변 생성"""
        try:
            # 1. 하이브리드 검색 수행
            search_results = await self._perform_search(request.query, request.max_results, db)
            
            # 2. 대화 히스토리 가져오기
            conversation_history = []
            if request.include_history and request.session_id:
                conversation_history = await self._get_conversation_history(
                    request.session_id, db
                )
            
            # 3. LLM으로 답변 생성
            llm_response = await self.llm_service.generate_response(
                user_message=request.query,
                context_documents=search_results,
                conversation_history=conversation_history
            )
            
            # 4. 출처 정보 추출
            sources = self._extract_sources(search_results)
            
            return RAGResponse(
                answer=llm_response.content,
                sources=sources,
                usage=llm_response.usage,
                model=llm_response.model,
                session_id=request.session_id or "new_session"
            )
            
        except Exception as e:
            logger.error(f"RAG 답변 생성 실패: {e}")
            raise

    async def generate_streaming_answer(
        self, 
        request: RAGRequest, 
        db: Session
    ) -> AsyncGenerator[str, None]:
        """RAG 기반 스트리밍 답변 생성"""
        try:
            # 1. 하이브리드 검색 수행
            search_results = await self._perform_search(request.query, request.max_results, db)
            
            # 2. 대화 히스토리 가져오기
            conversation_history = []
            if request.include_history and request.session_id:
                conversation_history = await self._get_conversation_history(
                    request.session_id, db
                )
            
            # 3. 스트리밍 답변 생성
            async for chunk in self.llm_service.generate_streaming_response(
                user_message=request.query,
                context_documents=search_results,
                conversation_history=conversation_history
            ):
                yield chunk
                
        except Exception as e:
            logger.error(f"RAG 스트리밍 답변 생성 실패: {e}")
            raise

    async def _perform_search(self, query: str, max_results: int, db: Session) -> List[Dict[str, str]]:
        """하이브리드 검색 수행"""
        try:
            # SearchService 인스턴스 생성
            search_service = SearchService(db)
            
            # 하이브리드 검색 실행
            search_results = search_service.hybrid_search(
                query=query,
                limit=max_results,
                alpha=0.7,  # Dense 검색 가중치
                beta=0.3    # BM25 검색 가중치
            )
            
            # 검색 결과를 문서 형태로 변환하고 문서 메타데이터 추가
            documents = []
            for result in search_results:
                # 원본 문서 정보 가져오기
                from ..models.document import Document
                document = db.query(Document).filter(Document.id == result["document_id"]).first()
                
                doc_info = {
                    "title": document.title if document else "제목 없음",
                    "content": result["chunk_text"],
                    "source": f"문서 ID: {result['document_id']}, 청크: {result['id']}",
                    "score": result.get("combined_score", 0.0),
                    "document_id": result["document_id"],
                    "chunk_index": result["id"],
                    "filename": result["filename"],
                    "file_size": document.file_size if document else 0,
                    "created_at": document.created_at.isoformat() if document and document.created_at else None,
                    "download_url": f"/api/v1/documents/{result['document_id']}/download" if document else None,
                    "preview_url": f"/api/v1/documents/{result['document_id']}/chunks?chunk_index={result['id']}" if document else None
                }
                documents.append(doc_info)
            
            return documents
            
        except Exception as e:
            logger.error(f"검색 수행 실패: {e}")
            return []

    async def _get_conversation_history(
        self, 
        session_id: str, 
        db: Session
    ) -> List[Dict[str, str]]:
        """대화 히스토리 가져오기"""
        try:
            from ..models.chat_session import ChatMessage
            
            # 최근 10개 메시지 가져오기
            messages = db.query(ChatMessage).filter(
                ChatMessage.session_id == session_id
            ).order_by(ChatMessage.created_at.desc()).limit(10).all()
            
            # 역순으로 정렬 (오래된 것부터)
            messages.reverse()
            
            history = []
            for msg in messages:
                history.append({
                    "role": "user" if msg.is_user else "assistant",
                    "content": msg.content
                })
            
            return history
            
        except Exception as e:
            logger.error(f"대화 히스토리 가져오기 실패: {e}")
            return []

    def _extract_sources(self, search_results: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """출처 정보 추출 (풍부한 메타데이터 포함)"""
        sources = []
        for i, result in enumerate(search_results, 1):
            source = {
                "index": i,
                "title": result["title"],
                "source": result["source"],
                "score": round(result.get("score", 0.0), 4),
                "document_id": result.get("document_id"),
                "chunk_index": result.get("chunk_index"),
                "filename": result.get("filename"),
                "file_size": result.get("file_size", 0),
                "created_at": result.get("created_at"),
                "download_url": result.get("download_url"),
                "preview_url": result.get("preview_url"),
                "content_preview": result["content"][:200] + "..." if len(result["content"]) > 200 else result["content"]
            }
            sources.append(source)
        return sources

    async def test_rag_pipeline(self, test_query: str = "안녕하세요", db: Session = None) -> Dict[str, any]:
        """RAG 파이프라인 테스트"""
        try:
            # 검색 테스트
            search_results = await self._perform_search(test_query, 3, db) if db else []
            
            # LLM 연결 테스트
            llm_connected = await self.llm_service.test_connection()
            
            return {
                "search_working": len(search_results) > 0,
                "llm_connected": llm_connected,
                "search_results_count": len(search_results),
                "test_query": test_query
            }
            
        except Exception as e:
            logger.error(f"RAG 파이프라인 테스트 실패: {e}")
            return {
                "search_working": False,
                "llm_connected": False,
                "error": str(e)
            }


# 전역 인스턴스
rag_service = RAGService()
