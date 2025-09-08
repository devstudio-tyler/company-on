"""
문서 관리 API 라우터
"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from ....database.connection import get_db
from ....services.document_service import DocumentService
from ....services.minio_service import minio_service
from ....services.upload_session_service import UploadSessionService
from ....services.sse_service import sse_service
from ....schemas.document import (
    DocumentUploadInitRequest,
    DocumentUploadInitResponse,
    DocumentUploadCommitRequest,
    DocumentUploadCommitResponse,
    DocumentResponse,
    DocumentListResponse,
    DocumentReprocessRequest,
    DocumentReprocessResponse,
    DocumentChunkListResponse,
    DocumentStatus,
    ErrorResponse
)
from ....schemas.upload_session import UploadStatus
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentUploadInitResponse)
async def init_document_upload(
    request: DocumentUploadInitRequest,
    db: Session = Depends(get_db)
):
    """
    문서 업로드 시작 (Init)
    
    파일 업로드를 위한 사전 서명된 URL을 생성하고 업로드 세션을 생성합니다.
    """
    try:
        # MinIO에서 업로드 URL 생성
        upload_id, upload_url = minio_service.generate_upload_url(
            filename=request.filename,
            expires_minutes=60
        )
        
        # 업로드 세션 생성
        upload_service = UploadSessionService(db)
        upload_service.create_upload_session(
            upload_id=upload_id,
            filename=request.filename,
            file_size=request.size,
            content_type=request.content_type
        )
        
        # 만료 시간 계산 (현재 시간 + 60분)
        from datetime import timedelta
        expires_at = datetime.utcnow().replace(microsecond=0) + timedelta(minutes=60)
        
        logger.info(f"Upload URL generated for: {request.filename}")
        
        return DocumentUploadInitResponse(
            upload_id=upload_id,
            upload_url=upload_url,
            expires_at=expires_at
        )
        
    except Exception as e:
        logger.error(f"Failed to generate upload URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate upload URL"
        )


@router.put("/upload/{upload_id}", response_model=DocumentUploadCommitResponse)
async def commit_document_upload(
    upload_id: str,
    request: DocumentUploadCommitRequest,
    db: Session = Depends(get_db)
):
    """
    문서 업로드 완료 (Commit)
    
    업로드된 파일을 데이터베이스에 등록하고 처리 작업을 시작합니다.
    """
    try:
        # 업로드 세션 확인
        upload_service = UploadSessionService(db)
        upload_session = upload_service.get_upload_session(upload_id)
        
        if not upload_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Upload session not found"
            )
        
        # MinIO에서 파일 정보 확인
        file_path = f"uploads/{upload_id}/{upload_session.filename}"
        
        if not minio_service.file_exists(file_path):
            # 업로드 실패 처리
            upload_service.fail_upload(upload_id, "Uploaded file not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Uploaded file not found"
            )
        
        # 문서 서비스로 문서 생성
        document_service = DocumentService(db)
        
        document = document_service.create_document(
            filename=upload_session.filename,
            file_size=upload_session.file_size,
            content_type=upload_session.content_type,
            file_path=file_path,
            metadata=request.metadata
        )
        
        # 업로드 세션 완료 처리
        upload_service.complete_upload(upload_id, document.id)
        
        # SSE로 상태 변경 알림
        await sse_service.broadcast_upload_status_change(upload_id, UploadStatus.PENDING)
        
        logger.info(f"Document uploaded and registered: {document.id}")
        
        return DocumentUploadCommitResponse(
            document_id=document.id,
            status=DocumentStatus.PROCESSING
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to commit document upload: {e}")
        # 업로드 실패 처리
        upload_service.fail_upload(upload_id, str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to commit document upload"
        )


@router.get("", response_model=DocumentListResponse)
async def get_documents(
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    status: Optional[DocumentStatus] = Query(None, description="문서 상태 필터"),
    search: Optional[str] = Query(None, description="검색어"),
    db: Session = Depends(get_db)
):
    """
    문서 목록 조회
    """
    try:
        document_service = DocumentService(db)
        documents, total = document_service.get_documents(
            page=page,
            limit=limit,
            status=status,
            search=search
        )
        
        return DocumentListResponse(
            documents=documents,
            total=total,
            page=page,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Failed to get documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get documents"
        )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    """
    문서 상세 조회
    """
    try:
        document_service = DocumentService(db)
        document = document_service.get_document(document_id)
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        return document
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get document"
        )


@router.get("/{document_id}/download")
async def download_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    """
    문서 다운로드
    """
    try:
        document_service = DocumentService(db)
        document = document_service.get_document(document_id)
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # MinIO에서 다운로드 URL 생성
        download_url = minio_service.get_file_url(document.file_path)
        
        return {"download_url": download_url}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate download URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate download URL"
        )


@router.post("/{document_id}/reprocess", response_model=DocumentReprocessResponse)
async def reprocess_document(
    document_id: int,
    request: DocumentReprocessRequest,
    db: Session = Depends(get_db)
):
    """
    문서 재처리
    """
    try:
        document_service = DocumentService(db)
        document = document_service.get_document(document_id)
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # TODO: Celery 워커로 재처리 작업 큐에 추가
        task_id = f"reprocess_{document_id}_{datetime.utcnow().timestamp()}"
        
        # 상태를 처리 중으로 변경
        document_service.update_document_status(document_id, DocumentStatus.PROCESSING)
        
        logger.info(f"Document reprocessing queued: {document_id}")
        
        return DocumentReprocessResponse(
            task_id=task_id,
            status="queued"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to queue document reprocessing: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to queue document reprocessing"
        )


@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    """
    문서 삭제
    """
    try:
        document_service = DocumentService(db)
        success = document_service.delete_document(document_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        return {"success": True, "deleted_at": datetime.utcnow()}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document"
        )


@router.get("/{document_id}/chunks", response_model=DocumentChunkListResponse)
async def get_document_chunks(
    document_id: int,
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    search: Optional[str] = Query(None, description="검색어"),
    chunk_index: Optional[int] = Query(None, description="특정 청크 인덱스 조회"),
    db: Session = Depends(get_db)
):
    """
    문서 청크 목록 조회
    """
    try:
        document_service = DocumentService(db)
        
        # 특정 청크 인덱스가 지정된 경우
        if chunk_index is not None:
            from ....models.document import DocumentChunk
            from ....schemas.document import DocumentChunkResponse
            
            # 특정 청크만 조회
            chunk = db.query(DocumentChunk).filter(
                DocumentChunk.document_id == document_id,
                DocumentChunk.chunk_index == chunk_index
            ).first()
            
            if not chunk:
                return DocumentChunkListResponse(chunks=[], total=0)
                
            chunk_response = DocumentChunkResponse(
                id=chunk.id,
                document_id=chunk.document_id,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                chunk_metadata=chunk.chunk_metadata,
                created_at=chunk.created_at
            )
            
            return DocumentChunkListResponse(
                chunks=[chunk_response],
                total=1
            )
        
        # 일반적인 청크 목록 조회
        chunks, total = document_service.get_document_chunks(
            document_id=document_id,
            page=page,
            limit=limit,
            search=search
        )
        
        return DocumentChunkListResponse(
            chunks=chunks,
            total=total
        )
        
    except Exception as e:
        logger.error(f"Failed to get document chunks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get document chunks"
        )
