"""
문서 처리 파이프라인 서비스
문서 업로드부터 벡터 DB 저장까지의 전체 파이프라인을 관리하는 서비스
"""
import os
import tempfile
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
import logging

from ..models.document import Document, DocumentChunk
from ..models.upload_session import UploadSession
from ..services.document_parser import DocumentParser
from ..services.text_chunker import TextChunker
from ..services.embedding_service import EmbeddingService
from ..services.minio_service import MinIOService
from ..services.sse_service import sse_service

logger = logging.getLogger(__name__)

class DocumentProcessingService:
    """문서 처리 파이프라인 서비스"""
    
    def __init__(self, db: Session):
        self.db = db
        self.parser = DocumentParser()
        self.chunker = TextChunker()
        self.embedding_service = EmbeddingService()
        self.minio_service = MinIOService()
    
    async def process_document_pipeline(self, upload_id: str) -> Dict[str, Any]:
        """
        문서 처리 파이프라인 실행
        
        Args:
            upload_id: 업로드 세션 ID
            
        Returns:
            처리 결과 정보
        """
        try:
            # 1단계: 업로드 세션 조회
            upload_session = self._get_upload_session(upload_id)
            if not upload_session:
                raise ValueError(f"업로드 세션을 찾을 수 없습니다: {upload_id}")
            
            # 상태 업데이트: 처리 시작
            await self._update_upload_status(upload_id, "processing", "문서 처리 시작")
            
            # 2단계: 파일 다운로드
            file_path = await self._download_file(upload_session)
            await self._update_upload_status(upload_id, "processing", "파일 다운로드 완료")
            
            # 3단계: 텍스트 추출
            parsed_data = await self._extract_text(file_path, upload_session.content_type)
            await self._update_upload_status(upload_id, "processing", "텍스트 추출 완료")
            
            # 4단계: 문서 레코드 생성
            document = await self._create_document_record(upload_session, parsed_data)
            await self._update_upload_status(upload_id, "processing", "문서 레코드 생성 완료")
            
            # 5단계: 텍스트 청킹
            chunks = await self._chunk_text(parsed_data["text"], document.id)
            await self._update_upload_status(upload_id, "processing", f"텍스트 청킹 완료 ({len(chunks)}개 청크)")
            
            # 6단계: 임베딩 생성 및 저장
            await self._generate_and_store_embeddings(chunks)
            await self._update_upload_status(upload_id, "processing", "임베딩 생성 및 저장 완료")
            
            # 7단계: 업로드 세션 완료 처리
            await self._complete_upload_session(upload_id, document.id)
            
            # 임시 파일 정리
            if os.path.exists(file_path):
                os.remove(file_path)
            
            logger.info(f"문서 처리 파이프라인 완료: {upload_id}")
            
            return {
                "success": True,
                "document_id": document.id,
                "chunks_created": len(chunks),
                "total_tokens": parsed_data["token_count"]
            }
            
        except Exception as e:
            logger.error(f"문서 처리 파이프라인 실패: {upload_id}, 에러: {str(e)}")
            await self._update_upload_status(upload_id, "failed", f"처리 실패: {str(e)}")
            raise
    
    def _get_upload_session(self, upload_id: str) -> Optional[UploadSession]:
        """업로드 세션 조회"""
        return self.db.query(UploadSession).filter(UploadSession.id == upload_id).first()
    
    async def _update_upload_status(self, upload_id: str, status: str, message: str = None):
        """업로드 상태 업데이트 및 SSE 알림"""
        try:
            upload_session = self._get_upload_session(upload_id)
            if upload_session:
                upload_session.status = status
                if message:
                    upload_session.error_message = message
                self.db.commit()
                
                # SSE로 상태 변경 알림
                await sse_service.broadcast_upload_status_change(
                    upload_id, status, upload_session.uploaded_size, 
                    upload_session.file_size, message
                )
                
        except Exception as e:
            logger.error(f"상태 업데이트 실패: {upload_id}, 에러: {str(e)}")
    
    async def _download_file(self, upload_session: UploadSession) -> str:
        """MinIO에서 파일 다운로드"""
        try:
            # 임시 파일 생성
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f".{upload_session.filename.split('.')[-1]}")
            temp_path = temp_file.name
            temp_file.close()
            
            # MinIO에서 파일 다운로드
            self.minio_service.download_file(upload_session.id, temp_path)
            
            return temp_path
            
        except Exception as e:
            logger.error(f"파일 다운로드 실패: {upload_session.id}, 에러: {str(e)}")
            raise
    
    async def _extract_text(self, file_path: str, content_type: str) -> Dict[str, Any]:
        """텍스트 추출"""
        try:
            # 파일 유효성 검증
            if not self.parser.validate_file(file_path, content_type):
                raise ValueError(f"파일 유효성 검증 실패: {file_path}")
            
            # 텍스트 추출
            parsed_data = self.parser.parse_document(file_path, content_type)
            
            logger.info(f"텍스트 추출 완료: {parsed_data['token_count']}개 토큰")
            
            return parsed_data
            
        except Exception as e:
            logger.error(f"텍스트 추출 실패: {file_path}, 에러: {str(e)}")
            raise
    
    async def _create_document_record(self, upload_session: UploadSession, parsed_data: Dict[str, Any]) -> Document:
        """문서 레코드 생성"""
        try:
            document = Document(
                filename=upload_session.filename,
                file_size=upload_session.file_size,
                content_type=upload_session.content_type,
                document_metadata=parsed_data["metadata"],
                created_at=upload_session.created_at
            )
            
            self.db.add(document)
            self.db.commit()
            self.db.refresh(document)
            
            logger.info(f"문서 레코드 생성 완료: {document.id}")
            
            return document
            
        except Exception as e:
            logger.error(f"문서 레코드 생성 실패: {str(e)}")
            raise
    
    async def _chunk_text(self, text: str, document_id: int) -> List[Dict[str, Any]]:
        """텍스트 청킹"""
        try:
            chunks = self.chunker.chunk_text(text, document_id)
            
            # 청크 통계 로깅
            stats = self.chunker.get_chunk_statistics(chunks)
            logger.info(f"텍스트 청킹 완료: {stats}")
            
            return chunks
            
        except Exception as e:
            logger.error(f"텍스트 청킹 실패: {str(e)}")
            raise
    
    async def _generate_and_store_embeddings(self, chunks: List[Dict[str, Any]]):
        """임베딩 생성 및 저장"""
        try:
            # 청크 텍스트 추출
            chunk_texts = [chunk["content"] for chunk in chunks]
            
            # 배치 임베딩 생성
            embeddings = self.embedding_service.generate_embeddings_batch(chunk_texts)
            
            # 임베딩 정규화
            normalized_embeddings = [
                self.embedding_service.normalize_embedding(embedding) 
                for embedding in embeddings
            ]
            
            # 데이터베이스에 청크 및 임베딩 저장
            for i, chunk in enumerate(chunks):
                document_chunk = DocumentChunk(
                    document_id=chunk["document_id"],
                    chunk_index=chunk["chunk_index"],
                    content=chunk["content"],
                    embedding=normalized_embeddings[i],
                    chunk_metadata=chunk["metadata"]
                )
                
                self.db.add(document_chunk)
            
            self.db.commit()
            
            logger.info(f"임베딩 생성 및 저장 완료: {len(chunks)}개 청크")
            
        except Exception as e:
            logger.error(f"임베딩 생성 및 저장 실패: {str(e)}")
            raise
    
    async def _complete_upload_session(self, upload_id: str, document_id: int):
        """업로드 세션 완료 처리"""
        try:
            upload_session = self._get_upload_session(upload_id)
            if upload_session:
                upload_session.status = "completed"
                upload_session.document_id = document_id
                upload_session.error_message = None
                self.db.commit()
                
                # SSE로 완료 알림
                await sse_service.broadcast_upload_status_change(
                    upload_id, "completed", upload_session.uploaded_size,
                    upload_session.file_size, "문서 처리 완료"
                )
                
        except Exception as e:
            logger.error(f"업로드 세션 완료 처리 실패: {str(e)}")
            raise
    
    def get_processing_status(self, upload_id: str) -> Optional[Dict[str, Any]]:
        """처리 상태 조회"""
        upload_session = self._get_upload_session(upload_id)
        if not upload_session:
            return None
        
        return {
            "upload_id": upload_session.id,
            "status": upload_session.status,
            "document_id": upload_session.document_id,
            "error_message": upload_session.error_message,
            "created_at": upload_session.created_at,
            "updated_at": upload_session.updated_at
        }
