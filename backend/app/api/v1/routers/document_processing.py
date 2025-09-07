"""
문서 처리 파이프라인 API
문서 업로드부터 벡터 DB 저장까지의 전체 파이프라인을 관리하는 API
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from ....database.connection import get_db
from ....services.document_processing_service import DocumentProcessingService
from ....services.upload_session_service import UploadSessionService
from ....schemas.document import ErrorResponse

router = APIRouter(prefix="/documents/processing", tags=["document_processing"])

@router.post("/start/{upload_id}", status_code=status.HTTP_202_ACCEPTED)
async def start_document_processing(
    upload_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    문서 처리 파이프라인을 시작합니다.
    
    - **upload_id**: 업로드 세션 ID
    - 백그라운드에서 전체 파이프라인 실행:
      1. 파일 다운로드
      2. 텍스트 추출
      3. 텍스트 청킹
      4. 임베딩 생성
      5. 벡터 DB 저장
    """
    try:
        # 업로드 세션 존재 확인
        upload_service = UploadSessionService(db)
        upload_session = upload_service.get_upload_session(upload_id)
        
        if not upload_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Upload session not found"
            )
        
        if upload_session.status not in ["pending", "init"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid upload session status: {upload_session.status}"
            )
        
        # 백그라운드에서 문서 처리 파이프라인 시작
        processing_service = DocumentProcessingService(db)
        background_tasks.add_task(
            processing_service.process_document_pipeline,
            upload_id
        )
        
        return {
            "message": "Document processing started",
            "upload_id": upload_id,
            "status": "processing"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start document processing: {str(e)}"
        )

@router.get("/status/{upload_id}")
async def get_processing_status(
    upload_id: str,
    db: Session = Depends(get_db)
):
    """
    문서 처리 상태를 조회합니다.
    
    - **upload_id**: 업로드 세션 ID
    """
    try:
        processing_service = DocumentProcessingService(db)
        status_info = processing_service.get_processing_status(upload_id)
        
        if not status_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Upload session not found"
            )
        
        return status_info
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get processing status: {str(e)}"
        )

@router.post("/retry/{upload_id}", status_code=status.HTTP_202_ACCEPTED)
async def retry_document_processing(
    upload_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    실패한 문서 처리를 재시도합니다.
    
    - **upload_id**: 업로드 세션 ID
    """
    try:
        # 업로드 세션 존재 확인
        upload_service = UploadSessionService(db)
        upload_session = upload_service.get_upload_session(upload_id)
        
        if not upload_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Upload session not found"
            )
        
        if upload_session.status != "failed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only retry failed upload sessions"
            )
        
        # 상태를 pending으로 변경
        upload_service.update_upload_session_status(
            upload_id=upload_id,
            status="pending",
            error_message=None
        )
        
        # 백그라운드에서 문서 처리 파이프라인 재시작
        processing_service = DocumentProcessingService(db)
        background_tasks.add_task(
            processing_service.process_document_pipeline,
            upload_id
        )
        
        return {
            "message": "Document processing retry started",
            "upload_id": upload_id,
            "status": "pending"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retry document processing: {str(e)}"
        )

@router.get("/stats")
async def get_processing_stats(db: Session = Depends(get_db)):
    """
    문서 처리 통계를 조회합니다.
    """
    try:
        upload_service = UploadSessionService(db)
        
        # 상태별 통계
        stats = upload_service.get_processing_statistics()
        
        return {
            "processing_statistics": stats,
            "total_sessions": sum(stats.values())
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get processing stats: {str(e)}"
        )
