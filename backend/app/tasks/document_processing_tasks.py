"""
문서 처리 관련 Celery 태스크
"""
import os
import logging
from typing import Dict, Any
from celery import current_task
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from ..database.connection import get_db_url
from ..services.document_processing_service import DocumentProcessingService
from ..services.sse_service import sse_service
from .celery_app import celery_app

logger = logging.getLogger(__name__)

# 데이터베이스 엔진 생성
engine = create_engine(get_db_url())
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@celery_app.task(bind=True, name="process_document_pipeline")
def process_document_pipeline_task(self, upload_id: str) -> Dict[str, Any]:
    """
    문서 처리 파이프라인을 실행하는 Celery 태스크
    
    Args:
        upload_id: 업로드 세션 ID
        
    Returns:
        처리 결과 정보
    """
    db = SessionLocal()
    
    try:
        logger.info(f"문서 처리 파이프라인 시작: {upload_id}")
        
        # 태스크 상태 업데이트
        self.update_state(
            state="PROGRESS",
            meta={
                "upload_id": upload_id,
                "status": "processing",
                "message": "문서 처리 파이프라인 시작",
                "progress": 0
            }
        )
        
        # 문서 처리 서비스 실행
        processing_service = DocumentProcessingService(db)
        
        # SSE로 상태 알림
        import asyncio
        asyncio.create_task(sse_service.broadcast_upload_status_change(
            upload_id, "processing", 0, 0, "문서 처리 파이프라인 시작"
        ))
        
        # 파이프라인 실행
        result = asyncio.run(processing_service.process_document_pipeline(upload_id))
        
        # 성공 상태 업데이트
        self.update_state(
            state="SUCCESS",
            meta={
                "upload_id": upload_id,
                "status": "completed",
                "message": "문서 처리 완료",
                "progress": 100,
                "result": result
            }
        )
        
        logger.info(f"문서 처리 파이프라인 완료: {upload_id}")
        
        return result
        
    except Exception as e:
        logger.error(f"문서 처리 파이프라인 실패: {upload_id}, 에러: {str(e)}")
        
        # 실패 상태 업데이트
        self.update_state(
            state="FAILURE",
            meta={
                "upload_id": upload_id,
                "status": "failed",
                "message": f"처리 실패: {str(e)}",
                "progress": 0,
                "error": str(e)
            }
        )
        
        # SSE로 실패 알림
        import asyncio
        asyncio.create_task(sse_service.broadcast_upload_status_change(
            upload_id, "failed", 0, 0, f"처리 실패: {str(e)}"
        ))
        
        raise
    
    finally:
        db.close()

@celery_app.task(bind=True, name="retry_document_processing")
def retry_document_processing_task(self, upload_id: str) -> Dict[str, Any]:
    """
    실패한 문서 처리를 재시도하는 태스크
    
    Args:
        upload_id: 업로드 세션 ID
        
    Returns:
        재시도 결과
    """
    logger.info(f"문서 처리 재시도 시작: {upload_id}")
    
    # 기존 태스크 취소 (있다면)
    # TODO: 기존 태스크 취소 로직 구현
    
    # 새로운 처리 태스크 시작
    return process_document_pipeline_task.delay(upload_id)

@celery_app.task(bind=True, name="cleanup_failed_processing")
def cleanup_failed_processing_task(self, upload_id: str) -> Dict[str, Any]:
    """
    실패한 문서 처리 정리 태스크
    
    Args:
        upload_id: 업로드 세션 ID
        
    Returns:
        정리 결과
    """
    db = SessionLocal()
    
    try:
        from ..services.upload_session_service import UploadSessionService
        
        upload_service = UploadSessionService(db)
        upload_session = upload_service.get_upload_session(upload_id)
        
        if upload_session and upload_session.status == "failed":
            # 실패한 세션 정리
            upload_service.delete_upload_session(upload_id)
            
            logger.info(f"실패한 업로드 세션 정리 완료: {upload_id}")
            
            return {
                "success": True,
                "message": f"업로드 세션 {upload_id} 정리 완료"
            }
        else:
            return {
                "success": False,
                "message": f"업로드 세션 {upload_id}를 찾을 수 없거나 이미 정리됨"
            }
            
    except Exception as e:
        logger.error(f"실패한 처리 정리 실패: {upload_id}, 에러: {str(e)}")
        raise
    
    finally:
        db.close()

@celery_app.task(bind=True, name="batch_process_documents")
def batch_process_documents_task(self, upload_ids: list) -> Dict[str, Any]:
    """
    여러 문서를 배치로 처리하는 태스크
    
    Args:
        upload_ids: 업로드 세션 ID 리스트
        
    Returns:
        배치 처리 결과
    """
    logger.info(f"배치 문서 처리 시작: {len(upload_ids)}개 문서")
    
    results = []
    successful = 0
    failed = 0
    
    for i, upload_id in enumerate(upload_ids):
        try:
            # 개별 문서 처리
            result = process_document_pipeline_task.delay(upload_id)
            results.append({
                "upload_id": upload_id,
                "task_id": result.id,
                "status": "started"
            })
            successful += 1
            
            # 진행률 업데이트
            progress = int((i + 1) / len(upload_ids) * 100)
            self.update_state(
                state="PROGRESS",
                meta={
                    "total": len(upload_ids),
                    "processed": i + 1,
                    "successful": successful,
                    "failed": failed,
                    "progress": progress
                }
            )
            
        except Exception as e:
            logger.error(f"배치 처리 중 오류: {upload_id}, 에러: {str(e)}")
            results.append({
                "upload_id": upload_id,
                "status": "failed",
                "error": str(e)
            })
            failed += 1
    
    logger.info(f"배치 문서 처리 완료: 성공 {successful}개, 실패 {failed}개")
    
    return {
        "total": len(upload_ids),
        "successful": successful,
        "failed": failed,
        "results": results
    }
