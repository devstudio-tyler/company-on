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
from ..services.excel_processing_service import ExcelProcessingService
from ..services.ocr_service import OCRService

logger = logging.getLogger(__name__)

class DocumentProcessingService:
    """문서 처리 파이프라인 서비스"""
    
    def __init__(self, db: Session):
        self.db = db
        self.parser = DocumentParser()
        self.chunker = TextChunker()
        self.embedding_service = EmbeddingService()
        self.minio_service = MinIOService()
        self.excel_processor = ExcelProcessingService()
        self.ocr_service = OCRService()
    
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
            
            # 4단계: 문서 레코드 확인 또는 생성
            document = await self._get_or_create_document_record(upload_session, parsed_data)
            await self._update_upload_status(upload_id, "processing", "문서 레코드 확인 완료")
            
            # 5단계: 텍스트 청킹
            if "chunks" in parsed_data:
                # 엑셀/CSV 파일의 경우 미리 생성된 청크 사용
                chunks = await self._create_chunks_from_excel_data(parsed_data["chunks"], document.id)
            else:
                # PDF/DOCX 파일의 경우 기존 청킹 로직 사용
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
            
            # 실패 유형에 따른 처리
            failure_type = self._determine_failure_type(e)
            await self._handle_processing_failure(upload_id, str(e), failure_type)
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
                
                # SSE로 상태 변경 알림 (upload_id, status 만 전달)
                await sse_service.broadcast_upload_status_change(upload_id, status)
                
        except Exception as e:
            logger.error(f"상태 업데이트 실패: {upload_id}, 에러: {str(e)}")
    
    async def _download_file(self, upload_session: UploadSession) -> str:
        """MinIO에서 파일 다운로드"""
        try:
            # MinIO 경로 계산
            from .minio_service import minio_service
            file_path = f"uploads/{upload_session.id}/{upload_session.filename}"

            # MinIO에서 파일 다운로드
            file_bytes = minio_service.download_file(file_path)
            if file_bytes is None:
                raise ValueError(f"파일 다운로드 실패: {file_path}")

            # 임시 파일 저장
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f".{upload_session.filename.split('.')[-1]}")
            temp_path = temp_file.name
            temp_file.close()
            with open(temp_path, 'wb') as f:
                f.write(file_bytes)

            logger.info(f"파일 다운로드 완료: {file_path} -> {temp_path}")

            return temp_path
            
        except Exception as e:
            logger.error(f"파일 다운로드 실패: {upload_session.id}, 에러: {str(e)}")
            raise
    
    async def _extract_text(self, file_path: str, content_type: str) -> Dict[str, Any]:
        """텍스트 추출"""
        try:
            # 이미지(JPG/PNG) 파일 처리 (OCR)
            if content_type in ['image/jpeg', 'image/png']:
                return await self._extract_image_text(file_path, content_type)
            
            # 엑셀/CSV 파일 처리
            if content_type in ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'text/csv']:
                return await self._extract_excel_text(file_path, content_type)
            
            # 기존 PDF/DOCX 파일 처리
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

    async def _extract_image_text(self, file_path: str, content_type: str) -> Dict[str, Any]:
        """이미지 파일에서 OCR로 텍스트 추출"""
        try:
            with open(file_path, 'rb') as f:
                image_bytes = f.read()
            ocr = self.ocr_service.extract_text(image_bytes)

            text = (ocr.get('text') or '').strip()
            metadata = ocr.get('metadata') or {}

            token_count = len(text.split())
            logger.info(f"이미지 OCR 텍스트 추출 완료: {token_count} tokens")

            return {
                'text': text,
                'metadata': {
                    **metadata,
                    'file_type': 'image',
                    'mime': content_type,
                },
                'token_count': token_count,
            }
        except Exception as e:
            logger.error(f"이미지 텍스트 추출 실패: {file_path}, 에러: {str(e)}")
            raise
    
    async def _extract_excel_text(self, file_path: str, content_type: str) -> Dict[str, Any]:
        """엑셀/CSV 파일 텍스트 추출"""
        try:
            # 파일 읽기
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            filename = os.path.basename(file_path)
            
            # 파일 타입별 처리
            if content_type == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
                chunks = self.excel_processor.process_excel_file(file_content, filename)
            elif content_type == 'text/csv':
                chunks = self.excel_processor.process_csv_file(file_content, filename)
            else:
                raise ValueError(f"지원하지 않는 파일 타입: {content_type}")
            
            # 청크 내용을 하나의 텍스트로 결합 (토큰 카운트용)
            full_text = "\n\n".join([chunk['content'] for chunk in chunks])
            
            # 토큰 수 추정 (대략적인 계산)
            token_count = len(full_text.split())
            
            logger.info(f"엑셀/CSV 텍스트 추출 완료: {len(chunks)}개 청크, {token_count}개 토큰")
            
            return {
                'text': full_text,
                'chunks': chunks,  # 청크 정보 포함
                'token_count': token_count,
                'metadata': {
                    'file_type': 'excel' if content_type == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' else 'csv',
                    'total_chunks': len(chunks)
                }
            }
            
        except Exception as e:
            logger.error(f"엑셀/CSV 텍스트 추출 실패: {file_path}, 에러: {str(e)}")
            raise
    
    async def _create_chunks_from_excel_data(self, excel_chunks: List[Dict[str, Any]], document_id: int) -> List[Dict[str, Any]]:
        """엑셀 데이터에서 청크 생성"""
        try:
            chunks = []
            
            for i, excel_chunk in enumerate(excel_chunks):
                chunk = {
                    "document_id": document_id,
                    "chunk_index": i,
                    "content": excel_chunk["content"],
                    "chunk_type": excel_chunk["chunk_type"],
                    "metadata": excel_chunk["chunk_metadata"]
                }
                chunks.append(chunk)
            
            logger.info(f"엑셀 데이터에서 {len(chunks)}개 청크 생성")
            return chunks
            
        except Exception as e:
            logger.error(f"엑셀 청크 생성 실패: {str(e)}")
            raise
    
    async def _get_or_create_document_record(self, upload_session: UploadSession, parsed_data: Dict[str, Any]) -> Document:
        """문서 레코드 조회 또는 생성"""
        try:
            # 이미 연결된 문서가 있는지 확인
            if upload_session.document_id:
                existing_document = self.db.query(Document).filter(Document.id == upload_session.document_id).first()
                if existing_document:
                    logger.info(f"기존 문서 레코드 사용: {existing_document.id}")
                    return existing_document
            
            # 새 문서 레코드 생성
            return await self._create_document_record(upload_session, parsed_data)
            
        except Exception as e:
            logger.error(f"문서 레코드 조회/생성 실패: {str(e)}")
            raise

    async def _create_document_record(self, upload_session: UploadSession, parsed_data: Dict[str, Any]) -> Document:
        """문서 레코드 생성"""
        try:
            # title과 file_path 설정 (nullable=False 필드들)
            title = upload_session.filename
            if title.endswith('.txt'):
                title = title[:-4]
            elif title.endswith('.pdf'):
                title = title[:-4]
            elif title.endswith('.docx'):
                title = title[:-5]
            
            file_path = f"uploads/{upload_session.id}/{upload_session.filename}"
            
            document = Document(
                title=title,
                filename=upload_session.filename,
                file_path=file_path,
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
                    chunk_type=chunk.get("chunk_type", "text"),  # 기본값은 "text"
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
            # 문서 상태 완료 처리
            document = self.db.query(Document).filter(Document.id == document_id).first()
            if document:
                document.status = "completed"
                self.db.commit()

            upload_session = self._get_upload_session(upload_id)
            if upload_session:
                upload_session.status = "completed"
                upload_session.document_id = document_id
                upload_session.error_message = None
                self.db.commit()
                
                # SSE로 완료 알림
                await sse_service.broadcast_upload_status_change(upload_id, "completed")
                
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
            "failure_type": upload_session.failure_type,
            "retryable": upload_session.retryable,
            "created_at": upload_session.created_at,
            "updated_at": upload_session.updated_at
        }
    
    def _determine_failure_type(self, error: Exception) -> str:
        """실패 유형 결정"""
        error_str = str(error).lower()
        
        # 업로드 관련 실패 (재처리 불가능)
        if any(keyword in error_str for keyword in [
            "file not found", "upload failed", "minio", "network", 
            "connection", "timeout", "file size", "unsupported format"
        ]):
            return "upload_failed"
        
        # 프로세싱 관련 실패 (재처리 가능)
        return "processing_failed"
    
    async def _handle_processing_failure(
        self, 
        upload_id: str, 
        error_message: str, 
        failure_type: str
    ):
        """처리 실패 처리"""
        try:
            from .upload_session_service import UploadSessionService
            from .document_service import DocumentService
            
            upload_service = UploadSessionService(self.db)
            document_service = DocumentService(self.db)
            
            # 업로드 세션 실패 처리
            upload_service.fail_upload(upload_id, error_message, failure_type)
            
            # 문서가 생성된 경우 문서도 실패 처리
            upload_session = self._get_upload_session(upload_id)
            if upload_session and upload_session.document_id:
                document_service.fail_document(
                    upload_session.document_id, 
                    error_message, 
                    failure_type
                )
            
            # SSE로 실패 알림
            await sse_service.broadcast_upload_status_change(upload_id, "failed")
            
        except Exception as e:
            logger.error(f"실패 처리 중 오류 발생: {upload_id}, 에러: {str(e)}")
