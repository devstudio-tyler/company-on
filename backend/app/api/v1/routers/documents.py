"""
문서 관리 API 라우터
"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File
from sqlalchemy.orm import Session
from ....database.connection import get_db
from ....services.document_service import DocumentService
from ....services.minio_service import minio_service
from fastapi.responses import RedirectResponse
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


@router.post("/upload-direct", response_model=DocumentUploadCommitResponse)
async def upload_file_direct(
    file: UploadFile = File(...),
    metadata: str = "{}",
    db: Session = Depends(get_db)
):
    """
    직접 파일 업로드 (CORS 문제 우회)
    
    multipart/form-data로 파일을 직접 업로드하고 처리를 시작합니다.
    """
    try:
        import json
        from io import BytesIO
        # 허용 MIME 타입 검증
        allowed_mimes = {
            'application/pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'text/csv',
            'image/png',
            'image/jpeg'
        }
        if (file.content_type or '').lower() not in allowed_mimes:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="지원되지 않는 파일 형식입니다.")
        
        # 메타데이터 파싱
        try:
            parsed_metadata = json.loads(metadata)
        except:
            parsed_metadata = {}
        
        # 파일 데이터 읽기
        file_content = await file.read()
        file_stream = BytesIO(file_content)
        
        # 고유 업로드 ID 생성
        import uuid
        upload_id = str(uuid.uuid4())
        file_path = f"uploads/{upload_id}/{file.filename}"
        
        # MinIO에 직접 업로드
        success = minio_service.upload_file(
            file_data=file_stream,
            file_path=file_path,
            content_type=file.content_type or "application/octet-stream"
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="파일 업로드 실패"
            )
        
        # 업로드 세션 생성
        upload_service = UploadSessionService(db)
        upload_service.create_upload_session(
            upload_id=upload_id,
            filename=file.filename or "unknown",
            file_size=len(file_content),
            content_type=file.content_type or "application/octet-stream"
        )
        
        # 문서 레코드 생성
        document_service = DocumentService(db)
        document = document_service.create_document(
            filename=file.filename or "unknown",
            file_size=len(file_content),
            content_type=file.content_type or "application/octet-stream",
            file_path=file_path,
            metadata=parsed_metadata
        )
        
        # 업로드 완료 처리
        upload_service.complete_upload(upload_id, document.id)
        
        # 처리 파이프라인 시작
        from ....tasks.document_processing_tasks import process_document_pipeline_task
        task = process_document_pipeline_task.delay(upload_id)
        
        logger.info(f"Direct upload completed: {document.id}, task: {task.id}")
        
        return DocumentUploadCommitResponse(
            document_id=document.id,
            status=DocumentStatus.PROCESSING
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Direct upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"업로드 실패: {str(e)}"
        )


@router.get("", response_model=DocumentListResponse)
async def get_documents(
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    doc_status: Optional[DocumentStatus] = Query(None, description="문서 상태 필터"),
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
            status=doc_status,
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
        
        # MinIO에서 파일 데이터 직접 다운로드
        file_data = minio_service.download_file(document.file_path)
        if not file_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found in storage"
            )
        
        # 파일 다운로드 응답 생성
        from fastapi.responses import Response
        from urllib.parse import quote
        
        # 파일명을 URL 인코딩하여 한글 파일명 지원
        encoded_filename = quote(document.filename.encode('utf-8'))
        
        return Response(
            content=file_data,
            media_type=document.content_type or "application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download file"
        )


@router.get("/{document_id}/file")
async def get_document_file(
    document_id: int,
    db: Session = Depends(get_db)
):
    """
    문서 파일 직접 반환 (프리뷰/임베딩용)
    """
    try:
        document_service = DocumentService(db)
        document = document_service.get_document(document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )

        # MinIO에서 파일 데이터 직접 다운로드
        file_data = minio_service.download_file(document.file_path)
        if not file_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found in storage"
            )
        
        # 파일 스트리밍 응답 생성
        from fastapi.responses import Response
        from urllib.parse import quote
        
        # 파일명을 URL 인코딩하여 한글 파일명 지원
        encoded_filename = quote(document.filename.encode('utf-8'))
        
        return Response(
            content=file_data,
            media_type=document.content_type or "application/octet-stream",
            headers={
                "Content-Disposition": f"inline; filename*=UTF-8''{encoded_filename}",
                "Cache-Control": "public, max-age=3600"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get file"
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


@router.post("/{document_id}/retry")
async def retry_document_processing(
    document_id: int,
    db: Session = Depends(get_db)
):
    """
    실패한 문서 처리 재시도
    """
    try:
        document_service = DocumentService(db)
        document = document_service.get_document(document_id)
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        if document.status != "failed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only failed documents can be retried"
            )
        
        # 문서 상태를 processing으로 변경
        document_service.update_document_status(document_id, "processing")
        
        # 처리 파이프라인 재시작
        upload_service = UploadSessionService(db)
        upload_sessions = upload_service.get_upload_sessions_by_document_id(document_id)
        
        if upload_sessions:
            upload_session = upload_sessions[0]
            from ....tasks.document_processing_tasks import process_document_pipeline_task
            task = process_document_pipeline_task.delay(upload_session.id)
            
            logger.info(f"Document processing retry started: {document_id}, task: {task.id}")
            
            return {
                "message": "Document processing retry started",
                "document_id": document_id,
                "task_id": task.id
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Upload session not found for this document"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retry document processing: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retry document processing"
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


@router.get("/{document_id}/excel-preview")
async def get_excel_preview(
    document_id: int,
    db: Session = Depends(get_db)
):
    """
    엑셀 파일 미리보기 (표 형태)
    """
    try:
        from ....models.document import Document, DocumentChunk
        import json
        
        # 문서 정보 조회
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # 엑셀/CSV 파일이 아닌 경우 에러
        if not (document.content_type in [
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'text/csv'
        ]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This endpoint only supports Excel and CSV files"
            )
        
        # 모든 청크 조회 (엑셀 데이터)
        chunks = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id,
            DocumentChunk.chunk_type == 'excel_sheet'
        ).order_by(DocumentChunk.chunk_index).all()
        
        if not chunks:
            return {
                "document_id": document_id,
                "filename": document.filename,
                "content_type": document.content_type,
                "sheets": []
            }
        
        # 청크 데이터를 시트별로 그룹화
        sheets_data = {}
        for chunk in chunks:
            metadata = chunk.chunk_metadata or {}
            sheet_name = metadata.get('sheet_name', 'Sheet1')
            
            if sheet_name not in sheets_data:
                sheets_data[sheet_name] = {
                    'sheet_name': sheet_name,
                    'headers': [],
                    'rows': [],
                    'total_rows': 0,
                    'total_columns': 0
                }
            
            # 청크 내용에서 헤더와 행 데이터 추출
            content_lines = chunk.content.split('\n')
            headers = []
            rows = []
            
            for line in content_lines:
                if line.startswith('컬럼:'):
                    # 헤더 추출: "컬럼: 이름, 나이, 직업"
                    headers = [h.strip() for h in line.replace('컬럼:', '').split(',')]
                    sheets_data[sheet_name]['headers'] = headers
                    sheets_data[sheet_name]['total_columns'] = len(headers)
                elif line.startswith('행 '):
                    # 행 데이터 추출: "행 2: 이름=김철수 | 나이=30 | 직업=개발자"
                    row_data = {}
                    row_text = line.split(':', 1)[1].strip()
                    if '|' in row_text:
                        pairs = row_text.split('|')
                        for pair in pairs:
                            if '=' in pair:
                                key, value = pair.split('=', 1)
                                row_data[key.strip()] = value.strip()
                    rows.append(row_data)
            
            sheets_data[sheet_name]['rows'].extend(rows)
            sheets_data[sheet_name]['total_rows'] = len(sheets_data[sheet_name]['rows'])
        
        # 시트 데이터를 리스트로 변환
        sheets = list(sheets_data.values())
        
        return {
            "document_id": document_id,
            "filename": document.filename,
            "content_type": document.content_type,
            "sheets": sheets
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get excel preview: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get excel preview"
        )
