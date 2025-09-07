"""
문서 관리 서비스
"""
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from ..models.document import Document, DocumentChunk
from ..schemas.document import DocumentStatus
from .minio_service import minio_service
import logging

logger = logging.getLogger(__name__)


class DocumentService:
    """문서 관리 서비스"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_document(
        self,
        filename: str,
        file_size: int,
        content_type: str,
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Document:
        """
        새 문서 생성
        
        Args:
            filename: 파일명
            file_size: 파일 크기
            content_type: MIME 타입
            file_path: MinIO 파일 경로
            metadata: 문서 메타데이터
            
        Returns:
            Document: 생성된 문서 객체
        """
        # 파일명에서 확장자 제거하여 제목 생성
        title = filename.rsplit('.', 1)[0] if '.' in filename else filename
        
        document = Document(
            title=title,
            filename=filename,
            file_path=file_path,
            file_size=file_size,
            content_type=content_type,
            status=DocumentStatus.PROCESSING,
            document_metadata=metadata
        )
        
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        
        logger.info(f"Document created: {document.id} - {filename}")
        return document
    
    def get_document(self, document_id: int) -> Optional[Document]:
        """
        문서 조회
        
        Args:
            document_id: 문서 ID
            
        Returns:
            Optional[Document]: 문서 객체 또는 None
        """
        return self.db.query(Document).filter(Document.id == document_id).first()
    
    def get_documents(
        self,
        page: int = 1,
        limit: int = 20,
        status: Optional[DocumentStatus] = None,
        search: Optional[str] = None
    ) -> tuple[List[Document], int]:
        """
        문서 목록 조회
        
        Args:
            page: 페이지 번호
            limit: 페이지당 항목 수
            status: 문서 상태 필터
            search: 검색어
            
        Returns:
            tuple: (문서 목록, 전체 개수)
        """
        query = self.db.query(Document)
        
        # 상태 필터
        if status:
            query = query.filter(Document.status == status)
        
        # 검색 필터
        if search:
            query = query.filter(
                Document.title.ilike(f"%{search}%") |
                Document.filename.ilike(f"%{search}%")
            )
        
        # 전체 개수
        total = query.count()
        
        # 페이지네이션
        documents = query.order_by(desc(Document.created_at)).offset((page - 1) * limit).limit(limit).all()
        
        return documents, total
    
    def update_document_status(self, document_id: int, status: DocumentStatus) -> bool:
        """
        문서 상태 업데이트
        
        Args:
            document_id: 문서 ID
            status: 새로운 상태
            
        Returns:
            bool: 업데이트 성공 여부
        """
        document = self.get_document(document_id)
        if not document:
            return False
        
        document.status = status
        document.updated_at = datetime.utcnow()
        
        self.db.commit()
        logger.info(f"Document status updated: {document_id} -> {status}")
        return True
    
    def update_document_metadata(self, document_id: int, metadata: Dict[str, Any]) -> bool:
        """
        문서 메타데이터 업데이트
        
        Args:
            document_id: 문서 ID
            metadata: 새로운 메타데이터
            
        Returns:
            bool: 업데이트 성공 여부
        """
        document = self.get_document(document_id)
        if not document:
            return False
        
        document.document_metadata = metadata
        document.updated_at = datetime.utcnow()
        
        self.db.commit()
        logger.info(f"Document metadata updated: {document_id}")
        return True
    
    def delete_document(self, document_id: int) -> bool:
        """
        문서 삭제
        
        Args:
            document_id: 문서 ID
            
        Returns:
            bool: 삭제 성공 여부
        """
        document = self.get_document(document_id)
        if not document:
            return False
        
        # MinIO에서 파일 삭제
        minio_service.delete_file(document.file_path)
        
        # 데이터베이스에서 문서 삭제 (CASCADE로 청크도 함께 삭제됨)
        self.db.delete(document)
        self.db.commit()
        
        logger.info(f"Document deleted: {document_id}")
        return True
    
    def get_document_chunks(
        self,
        document_id: int,
        page: int = 1,
        limit: int = 20,
        search: Optional[str] = None
    ) -> tuple[List[DocumentChunk], int]:
        """
        문서 청크 목록 조회
        
        Args:
            document_id: 문서 ID
            page: 페이지 번호
            limit: 페이지당 항목 수
            search: 검색어
            
        Returns:
            tuple: (청크 목록, 전체 개수)
        """
        query = self.db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id)
        
        # 검색 필터
        if search:
            query = query.filter(DocumentChunk.content.ilike(f"%{search}%"))
        
        # 전체 개수
        total = query.count()
        
        # 페이지네이션
        chunks = query.order_by(DocumentChunk.chunk_index).offset((page - 1) * limit).limit(limit).all()
        
        return chunks, total
    
    def create_document_chunk(
        self,
        document_id: int,
        chunk_index: int,
        content: str,
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None
    ) -> DocumentChunk:
        """
        문서 청크 생성
        
        Args:
            document_id: 문서 ID
            chunk_index: 청크 인덱스
            content: 청크 내용
            embedding: 임베딩 벡터
            metadata: 청크 메타데이터
            
        Returns:
            DocumentChunk: 생성된 청크 객체
        """
        chunk = DocumentChunk(
            document_id=document_id,
            chunk_index=chunk_index,
            content=content,
            embedding=embedding,
            chunk_metadata=metadata
        )
        
        self.db.add(chunk)
        self.db.commit()
        self.db.refresh(chunk)
        
        logger.info(f"Document chunk created: {chunk.id} for document {document_id}")
        return chunk
