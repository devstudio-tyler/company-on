"""
업로드 상태 추적 API 라우터
"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from ....database.connection import get_db
from ....services.upload_session_service import UploadSessionService
from ....services.sse_service import sse_service
from ....schemas.upload_session import (
    UploadSessionResponse,
    UploadSessionListResponse,
    UploadProgressResponse,
    UploadStatus,
    UploadStatusUpdateRequest
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/uploads", tags=["upload-status"])


@router.get("/sessions", response_model=UploadSessionListResponse)
async def get_upload_sessions(
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    status: Optional[UploadStatus] = Query(None, description="상태 필터"),
    db: Session = Depends(get_db)
):
    """
    업로드 세션 목록 조회
    """
    try:
        upload_service = UploadSessionService(db)
        sessions, total = upload_service.get_upload_sessions(
            page=page,
            limit=limit,
            status=status
        )
        
        return UploadSessionListResponse(
            sessions=sessions,
            total=total,
            page=page,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Failed to get upload sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get upload sessions"
        )


@router.get("/sessions/{upload_id}", response_model=UploadSessionResponse)
async def get_upload_session(
    upload_id: str,
    db: Session = Depends(get_db)
):
    """
    특정 업로드 세션 조회
    """
    try:
        upload_service = UploadSessionService(db)
        session = upload_service.get_upload_session(upload_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Upload session not found"
            )
        
        return session
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get upload session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get upload session"
        )


@router.get("/sessions/{upload_id}/progress", response_model=UploadProgressResponse)
async def get_upload_progress(
    upload_id: str,
    db: Session = Depends(get_db)
):
    """
    업로드 진행률 조회
    """
    try:
        upload_service = UploadSessionService(db)
        session = upload_service.get_upload_session(upload_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Upload session not found"
            )
        
        # 진행률 계산
        progress_percentage = 0
        if session.file_size > 0:
            progress_percentage = (session.uploaded_size / session.file_size) * 100
        
        return UploadProgressResponse(
            upload_id=session.id,
            filename=session.filename,
            status=session.status,
            progress_percentage=progress_percentage,
            uploaded_size=session.uploaded_size,
            file_size=session.file_size,
            document_id=session.document_id,
            error_message=session.error_message,
            updated_at=session.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get upload progress: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get upload progress"
        )


@router.get("/sessions/{upload_id}/stream")
async def stream_upload_status(
    upload_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    업로드 상태 실시간 스트리밍 (SSE)
    """
    try:
        upload_service = UploadSessionService(db)
        session = upload_service.get_upload_session(upload_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Upload session not found"
            )
        
        async def event_generator():
            # SSE 연결 설정
            await sse_service.add_upload_connection(upload_id, request)
            
            try:
                # 초기 상태 전송
                progress_data = UploadProgressResponse(
                    upload_id=session.id,
                    filename=session.filename,
                    status=session.status,
                    progress_percentage=(session.uploaded_size / session.file_size) * 100 if session.file_size > 0 else 0,
                    uploaded_size=session.uploaded_size,
                    file_size=session.file_size,
                    document_id=session.document_id,
                    error_message=session.error_message,
                    updated_at=session.updated_at
                )
                
                yield f"data: {progress_data.model_dump_json()}\n\n"
                
                # 연결 유지
                while True:
                    if await request.is_disconnected():
                        break
                    
                    await asyncio.sleep(1)  # 1초마다 체크
                    
            except Exception as e:
                logger.error(f"SSE stream error: {e}")
            finally:
                # 연결 정리
                await sse_service.remove_upload_connection(upload_id, request)
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to stream upload status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to stream upload status"
        )


@router.put("/sessions/{upload_id}/status")
async def update_upload_status(
    upload_id: str,
    status_update: UploadStatusUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    업로드 상태 업데이트 (내부 API)
    """
    try:
        upload_service = UploadSessionService(db)
        success = upload_service.update_upload_status(
            upload_id=upload_id,
            status=status_update.status,
            uploaded_size=status_update.uploaded_size,
            document_id=status_update.document_id,
            error_message=status_update.error_message
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Upload session not found"
            )
        
        # SSE로 상태 변경 알림
        await sse_service.broadcast_upload_status_change(upload_id, status_update.status)
        
        return {"success": True, "updated_at": datetime.utcnow()}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update upload status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update upload status"
        )


@router.delete("/sessions/{upload_id}")
async def delete_upload_session(
    upload_id: str,
    db: Session = Depends(get_db)
):
    """
    업로드 세션 삭제
    """
    try:
        upload_service = UploadSessionService(db)
        success = upload_service.delete_upload_session(upload_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Upload session not found"
            )
        
        return {"success": True, "deleted_at": datetime.utcnow()}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete upload session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete upload session"
        )
