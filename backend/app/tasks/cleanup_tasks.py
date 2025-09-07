"""
정리 관련 Celery 태스크
"""
import logging
from typing import Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, and_

from ..database.connection import get_db_url
from .celery_app import celery_app

logger = logging.getLogger(__name__)

# 데이터베이스 엔진 생성
engine = create_engine(get_db_url())
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@celery_app.task(bind=True, name="cleanup_old_sessions")
def cleanup_old_sessions_task(self, days_old: int = 30) -> Dict[str, Any]:
    """
    오래된 세션을 정리하는 태스크 (주기적 실행)
    
    Args:
        days_old: 정리할 세션의 최소 일수
        
    Returns:
        정리 결과
    """
    db = SessionLocal()
    
    try:
        # 오래된 세션 조회
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        from ..models.chat import ChatSession
        old_sessions = db.query(ChatSession).filter(
            and_(
                ChatSession.created_at < cutoff_date,
                ChatSession.status == "deleted"
            )
        ).all()
        
        deleted_count = 0
        for session in old_sessions:
            db.delete(session)
            deleted_count += 1
        
        db.commit()
        
        logger.info(f"오래된 세션 정리 완료: {deleted_count}개 세션 삭제")
        
        return {
            "success": True,
            "deleted_count": deleted_count,
            "cutoff_date": cutoff_date.isoformat()
        }
        
    except Exception as e:
        logger.error(f"오래된 세션 정리 실패: {str(e)}")
        raise
    
    finally:
        db.close()

@celery_app.task(bind=True, name="cleanup_failed_uploads")
def cleanup_failed_uploads_task(self, days_old: int = 7) -> Dict[str, Any]:
    """
    실패한 업로드를 정리하는 태스크
    
    Args:
        days_old: 정리할 업로드의 최소 일수
        
    Returns:
        정리 결과
    """
    db = SessionLocal()
    
    try:
        # 실패한 업로드 조회
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        from ..models.upload_session import UploadSession
        failed_uploads = db.query(UploadSession).filter(
            and_(
                UploadSession.created_at < cutoff_date,
                UploadSession.status == "failed"
            )
        ).all()
        
        deleted_count = 0
        for upload in failed_uploads:
            db.delete(upload)
            deleted_count += 1
        
        db.commit()
        
        logger.info(f"실패한 업로드 정리 완료: {deleted_count}개 업로드 삭제")
        
        return {
            "success": True,
            "deleted_count": deleted_count,
            "cutoff_date": cutoff_date.isoformat()
        }
        
    except Exception as e:
        logger.error(f"실패한 업로드 정리 실패: {str(e)}")
        raise
    
    finally:
        db.close()

@celery_app.task(bind=True, name="cleanup_orphaned_chunks")
def cleanup_orphaned_chunks_task(self) -> Dict[str, Any]:
    """
    고아가 된 문서 청크를 정리하는 태스크
    
    Returns:
        정리 결과
    """
    db = SessionLocal()
    
    try:
        from ..models.document import DocumentChunk, Document
        
        # 고아 청크 조회 (문서가 삭제된 청크)
        orphaned_chunks = db.query(DocumentChunk).outerjoin(
            Document, DocumentChunk.document_id == Document.id
        ).filter(Document.id.is_(None)).all()
        
        deleted_count = 0
        for chunk in orphaned_chunks:
            db.delete(chunk)
            deleted_count += 1
        
        db.commit()
        
        logger.info(f"고아 청크 정리 완료: {deleted_count}개 청크 삭제")
        
        return {
            "success": True,
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        logger.error(f"고아 청크 정리 실패: {str(e)}")
        raise
    
    finally:
        db.close()

@celery_app.task(bind=True, name="cleanup_old_embeddings")
def cleanup_old_embeddings_task(self, days_old: int = 90) -> Dict[str, Any]:
    """
    오래된 임베딩을 정리하는 태스크
    
    Args:
        days_old: 정리할 임베딩의 최소 일수
        
    Returns:
        정리 결과
    """
    db = SessionLocal()
    
    try:
        # 오래된 임베딩 조회
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        from ..models.chat import ChatSessionEmbedding
        old_embeddings = db.query(ChatSessionEmbedding).filter(
            ChatSessionEmbedding.created_at < cutoff_date
        ).all()
        
        deleted_count = 0
        for embedding in old_embeddings:
            db.delete(embedding)
            deleted_count += 1
        
        db.commit()
        
        logger.info(f"오래된 임베딩 정리 완료: {deleted_count}개 임베딩 삭제")
        
        return {
            "success": True,
            "deleted_count": deleted_count,
            "cutoff_date": cutoff_date.isoformat()
        }
        
    except Exception as e:
        logger.error(f"오래된 임베딩 정리 실패: {str(e)}")
        raise
    
    finally:
        db.close()

@celery_app.task(bind=True, name="system_health_check")
def system_health_check_task(self) -> Dict[str, Any]:
    """
    시스템 상태를 확인하는 태스크
    
    Returns:
        시스템 상태 정보
    """
    db = SessionLocal()
    
    try:
        from ..models.document import Document, DocumentChunk
        from ..models.chat import ChatSession, ChatMessage
        from ..models.upload_session import UploadSession
        
        # 데이터베이스 통계
        stats = {
            "documents": db.query(Document).count(),
            "document_chunks": db.query(DocumentChunk).count(),
            "chat_sessions": db.query(ChatSession).count(),
            "chat_messages": db.query(ChatMessage).count(),
            "upload_sessions": db.query(UploadSession).count(),
        }
        
        # 상태별 업로드 세션 통계
        from sqlalchemy import func
        upload_stats = db.query(
            UploadSession.status,
            func.count(UploadSession.id).label('count')
        ).group_by(UploadSession.status).all()
        
        upload_status_stats = {stat.status: stat.count for stat in upload_stats}
        
        logger.info(f"시스템 상태 확인 완료: {stats}")
        
        return {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "database_stats": stats,
            "upload_status_stats": upload_status_stats,
            "health": "healthy"
        }
        
    except Exception as e:
        logger.error(f"시스템 상태 확인 실패: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "health": "unhealthy"
        }
    
    finally:
        db.close()
