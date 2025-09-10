"""
채팅 관련 Celery 태스크
"""
import logging
from typing import Dict, Any, List
from celery import current_task
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from ..database.connection import get_db_url
from ..services.chat_session_service import ChatSessionService
from ..services.embedding_service import EmbeddingService
from ..celery_app import celery_app

logger = logging.getLogger(__name__)

# 데이터베이스 엔진 생성
engine = create_engine(get_db_url())
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@celery_app.task(bind=True, name="generate_session_summary")
def generate_session_summary_task(self, session_id: int, client_id: str) -> Dict[str, Any]:
    """
    채팅 세션 요약을 생성하는 태스크
    
    Args:
        session_id: 세션 ID
        client_id: 클라이언트 ID
        
    Returns:
        요약 생성 결과
    """
    db = SessionLocal()
    
    try:
        logger.info(f"세션 요약 생성 시작: 세션 {session_id}")
        
        # 세션 조회
        chat_service = ChatSessionService(db)
        session = chat_service.get_chat_session(session_id, client_id)
        
        if not session:
            raise ValueError(f"세션을 찾을 수 없습니다: {session_id}")
        
        # 메시지 조회
        from ..services.chat_message_service import ChatMessageService
        message_service = ChatMessageService(db)
        messages = message_service.get_recent_messages(session_id, client_id, limit=50)
        
        if not messages:
            return {
                "success": False,
                "message": "요약할 메시지가 없습니다"
            }
        
        # 메시지 텍스트 추출
        message_texts = [msg.content for msg in messages]
        conversation_text = "\n".join(message_texts)
        
        # 간단한 요약 생성 (향후 LLM 통합 시 확장)
        summary = f"총 {len(messages)}개의 메시지가 있는 대화입니다. 주요 주제: {session.title}"
        
        # 세션 업데이트
        from ..schemas.chat import ChatSessionUpdateRequest
        update_request = ChatSessionUpdateRequest(description=summary)
        chat_service.update_chat_session(session_id, client_id, update_request)
        
        logger.info(f"세션 요약 생성 완료: 세션 {session_id}")
        
        return {
            "success": True,
            "session_id": session_id,
            "summary": summary,
            "message_count": len(messages)
        }
        
    except Exception as e:
        logger.error(f"세션 요약 생성 실패: 세션 {session_id}, 에러: {str(e)}")
        raise
    
    finally:
        db.close()

@celery_app.task(bind=True, name="generate_session_embedding")
def generate_session_embedding_task(self, session_id: int, client_id: str) -> Dict[str, Any]:
    """
    채팅 세션 임베딩을 생성하는 태스크
    
    Args:
        session_id: 세션 ID
        client_id: 클라이언트 ID
        
    Returns:
        임베딩 생성 결과
    """
    db = SessionLocal()
    
    try:
        logger.info(f"세션 임베딩 생성 시작: 세션 {session_id}")
        
        # 세션 조회
        chat_service = ChatSessionService(db)
        session = chat_service.get_chat_session(session_id, client_id)
        
        if not session:
            raise ValueError(f"세션을 찾을 수 없습니다: {session_id}")
        
        # 메시지 조회
        from ..services.chat_message_service import ChatMessageService
        message_service = ChatMessageService(db)
        messages = message_service.get_recent_messages(session_id, client_id, limit=100)
        
        if not messages:
            return {
                "success": False,
                "message": "임베딩을 생성할 메시지가 없습니다"
            }
        
        # 세션 텍스트 생성
        session_text = f"{session.title}\n{session.description or ''}\n"
        message_texts = [f"{msg.role}: {msg.content}" for msg in messages]
        session_text += "\n".join(message_texts)
        
        # 임베딩 생성
        embedding_service = EmbeddingService()
        embedding = embedding_service.generate_embedding(session_text)
        normalized_embedding = embedding_service.normalize_embedding(embedding)
        
        # 임베딩 저장
        from ..models.chat import ChatSessionEmbedding
        existing_embedding = db.query(ChatSessionEmbedding).filter(
            ChatSessionEmbedding.session_id == session_id
        ).first()
        
        if existing_embedding:
            existing_embedding.embedding = normalized_embedding
        else:
            new_embedding = ChatSessionEmbedding(
                session_id=session_id,
                embedding=normalized_embedding,
                model_name=embedding_service.model_name
            )
            db.add(new_embedding)
        
        db.commit()
        
        logger.info(f"세션 임베딩 생성 완료: 세션 {session_id}")
        
        return {
            "success": True,
            "session_id": session_id,
            "embedding_dimension": len(normalized_embedding),
            "model_name": embedding_service.model_name
        }
        
    except Exception as e:
        logger.error(f"세션 임베딩 생성 실패: 세션 {session_id}, 에러: {str(e)}")
        raise
    
    finally:
        db.close()

@celery_app.task(bind=True, name="cleanup_old_sessions")
def cleanup_old_sessions_task(self, days_old: int = 30) -> Dict[str, Any]:
    """
    오래된 세션을 정리하는 태스크
    
    Args:
        days_old: 정리할 세션의 최소 일수
        
    Returns:
        정리 결과
    """
    db = SessionLocal()
    
    try:
        from datetime import datetime, timedelta
        from sqlalchemy import and_
        
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

@celery_app.task(bind=True, name="batch_generate_embeddings")
def batch_generate_embeddings_task(self, session_ids: List[int], client_id: str) -> Dict[str, Any]:
    """
    여러 세션의 임베딩을 배치로 생성하는 태스크
    
    Args:
        session_ids: 세션 ID 리스트
        client_id: 클라이언트 ID
        
    Returns:
        배치 처리 결과
    """
    logger.info(f"배치 임베딩 생성 시작: {len(session_ids)}개 세션")
    
    results = []
    successful = 0
    failed = 0
    
    for i, session_id in enumerate(session_ids):
        try:
            # 개별 세션 임베딩 생성
            result = generate_session_embedding_task.delay(session_id, client_id)
            results.append({
                "session_id": session_id,
                "task_id": result.id,
                "status": "started"
            })
            successful += 1
            
            # 진행률 업데이트
            progress = int((i + 1) / len(session_ids) * 100)
            self.update_state(
                state="PROGRESS",
                meta={
                    "total": len(session_ids),
                    "processed": i + 1,
                    "successful": successful,
                    "failed": failed,
                    "progress": progress
                }
            )
            
        except Exception as e:
            logger.error(f"배치 임베딩 생성 중 오류: 세션 {session_id}, 에러: {str(e)}")
            results.append({
                "session_id": session_id,
                "status": "failed",
                "error": str(e)
            })
            failed += 1
    
    logger.info(f"배치 임베딩 생성 완료: 성공 {successful}개, 실패 {failed}개")
    
    return {
        "total": len(session_ids),
        "successful": successful,
        "failed": failed,
        "results": results
    }
