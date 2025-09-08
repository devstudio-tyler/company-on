"""
채팅 API 라우터
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
import uuid
import json
import asyncio
import logging
from datetime import datetime

from ....database import get_db
from ....services.rag_service import rag_service
from ....services.sse_service import sse_service
from ....schemas.chat import (
    ChatMessageRequest,
    ChatMessageResponse,
    ChatSessionRequest,
    ChatSessionResponse,
    ChatSessionListResponse,
    ChatMessageListResponse,
    ChatMessageFeedbackRequest,
    ChatMessageFeedbackResponse,
    FeedbackType,
    RAGTestResponse
)
from ....models.chat import ChatSession, ChatMessage

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/chat/messages", response_model=ChatMessageResponse)
async def create_chat_message(
    request: ChatMessageRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """채팅 메시지 생성 및 RAG 응답"""
    try:
        # 세션 확인 또는 생성
        session = await _get_or_create_session(request.client_id, request.session_id, db)
        
        # 사용자 메시지 저장
        user_message = ChatMessage(
            session_id=session.id,
            role='user',
            content=request.content,
            created_at=datetime.utcnow()
        )
        db.add(user_message)
        db.commit()
        
        # RAG 응답 생성
        from ....services.rag_service import RAGRequest
        rag_request = RAGRequest(
            query=request.content,
            client_id=request.client_id,
            session_id=str(session.id),
            max_results=request.max_results,
            include_history=request.include_history
        )
        
        rag_response = await rag_service.generate_answer(rag_request, db)
        
        # AI 응답 메시지 저장
        ai_message = ChatMessage(
            session_id=session.id,
            role='assistant',
            content=rag_response.answer,
            created_at=datetime.utcnow()
        )
        db.add(ai_message)
        
        # 세션 업데이트
        session.updated_at = datetime.utcnow()
        db.commit()
        
        return ChatMessageResponse(
            message_id=str(ai_message.id),
            content=rag_response.answer,
            is_user=False,
            session_id=str(session.id),
            client_id=request.client_id,
            sources=rag_response.sources,
            usage=rag_response.usage,
            model=rag_response.model,
            created_at=ai_message.created_at
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"채팅 메시지 생성 실패: {str(e)}")


@router.post("/chat/messages/stream")
async def create_chat_message_stream(
    request: ChatMessageRequest,
    db: Session = Depends(get_db)
):
    """채팅 메시지 스트리밍 응답"""
    try:
        # 세션 확인 또는 생성
        session = await _get_or_create_session(request.client_id, request.session_id, db)
        
        # 사용자 메시지 저장
        user_message = ChatMessage(
            session_id=session.id,
            role='user',
            content=request.content,
            created_at=datetime.utcnow()
        )
        db.add(user_message)
        db.commit()
        
        # RAG 스트리밍 응답 생성
        from ....services.rag_service import RAGRequest
        rag_request = RAGRequest(
            query=request.content,
            client_id=request.client_id,
            session_id=str(session.id),
            max_results=request.max_results,
            include_history=request.include_history
        )
        
        async def generate_stream():
            try:
                # 1. 검색 수행하여 출처 정보 먼저 전송
                search_results = await rag_service._perform_search(rag_request.query, rag_request.max_results, db)
                
                # 출처 정보 먼저 전송
                if search_results:
                    sources = rag_service._extract_sources(search_results)
                    yield f"data: {json.dumps({'type': 'sources', 'sources': sources})}\n\n"
                
                # 2. 실제 LLM 스트리밍 응답 생성
                full_response = ""
                async for chunk in rag_service.generate_streaming_answer(rag_request, db):
                    if chunk:  # 빈 청크 건너뛰기
                        full_response += chunk
                        yield f"data: {json.dumps({'content': chunk, 'type': 'chunk'})}\n\n"
                
                # 3. 완료된 응답 저장
                ai_message = ChatMessage(
                    session_id=session.id,
                    role='assistant',
                    content=full_response,
                    created_at=datetime.utcnow()
                )
                db.add(ai_message)
                
                # 세션 업데이트
                session.updated_at = datetime.utcnow()
                db.commit()
                
                # 완료 신호
                yield f"data: {json.dumps({'type': 'complete', 'message_id': str(ai_message.id)})}\n\n"
                
            except Exception as e:
                logger.error(f"스트리밍 응답 생성 실패: {e}")
                yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"스트리밍 응답 생성 실패: {str(e)}")


@router.post("/chat/sessions", response_model=ChatSessionResponse)
async def create_chat_session(
    request: ChatSessionRequest,
    db: Session = Depends(get_db)
):
    """채팅 세션 생성"""
    try:
        session = ChatSession(
            client_id=request.client_id,
            title=request.title or f"새 대화 {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(session)
        db.commit()
        db.refresh(session)
        
        return ChatSessionResponse(
            session_id=str(session.id),
            client_id=str(session.client_id),
            title=session.title,
            created_at=session.created_at,
            updated_at=session.updated_at,
            message_count=0
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"채팅 세션 생성 실패: {str(e)}")


@router.get("/chat/sessions", response_model=ChatSessionListResponse)
async def get_chat_sessions(
    client_id: str,
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db)
):
    """채팅 세션 목록 조회"""
    try:
        offset = (page - 1) * size
        
        sessions = db.query(ChatSession).filter(
            ChatSession.client_id == client_id
        ).order_by(ChatSession.updated_at.desc()).offset(offset).limit(size).all()
        
        total = db.query(ChatSession).filter(
            ChatSession.client_id == client_id
        ).count()
        
        session_responses = []
        for session in sessions:
            message_count = db.query(ChatMessage).filter(
                ChatMessage.session_id == session.id
            ).count()
            
            session_responses.append(ChatSessionResponse(
                session_id=str(session.id),
                client_id=str(session.client_id),
                title=session.title,
                created_at=session.created_at,
                updated_at=session.updated_at,
                message_count=message_count
            ))
        
        return ChatSessionListResponse(
            sessions=session_responses,
            total=total,
            page=page,
            size=size
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"채팅 세션 조회 실패: {str(e)}")


@router.get("/chat/sessions/{session_id}/messages", response_model=ChatMessageListResponse)
async def get_chat_messages(
    session_id: str,
    page: int = 1,
    size: int = 50,
    db: Session = Depends(get_db)
):
    """채팅 메시지 목록 조회"""
    try:
        offset = (page - 1) * size
        
        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == int(session_id)
        ).order_by(ChatMessage.created_at.asc()).offset(offset).limit(size).all()
        
        total = db.query(ChatMessage).filter(
            ChatMessage.session_id == int(session_id)
        ).count()
        
        message_responses = []
        for message in messages:
            message_responses.append(ChatMessageResponse(
                message_id=str(message.id),
                content=message.content,
                is_user=(message.role == 'user'),
                session_id=str(message.session_id),
                client_id="",  # 메시지에는 client_id가 없으므로 빈 문자열
                sources=[],  # 메시지 저장 시에는 sources 정보가 없음
                usage={},    # 메시지 저장 시에는 usage 정보가 없음
                model="",    # 메시지 저장 시에는 model 정보가 없음
                created_at=message.created_at
            ))
        
        return ChatMessageListResponse(
            messages=message_responses,
            total=total,
            page=page,
            size=size
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"채팅 메시지 조회 실패: {str(e)}")


@router.delete("/chat/sessions/{session_id}")
async def delete_chat_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """채팅 세션 삭제"""
    try:
        # 세션 확인
        session = db.query(ChatSession).filter(ChatSession.id == int(session_id)).first()
        if not session:
            raise HTTPException(status_code=404, detail="채팅 세션을 찾을 수 없습니다")
        
        # 관련 메시지 삭제
        db.query(ChatMessage).filter(ChatMessage.session_id == int(session_id)).delete()
        
        # 세션 삭제
        db.delete(session)
        db.commit()
        
        return {"message": "채팅 세션이 삭제되었습니다"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"채팅 세션 삭제 실패: {str(e)}")


@router.post("/chat/messages/{message_id}/feedback", response_model=ChatMessageFeedbackResponse)
async def update_message_feedback(
    message_id: str,
    request: ChatMessageFeedbackRequest,
    db: Session = Depends(get_db)
):
    """채팅 메시지 피드백 업데이트"""
    try:
        # 메시지 확인
        message = db.query(ChatMessage).filter(ChatMessage.id == int(message_id)).first()
        if not message:
            raise HTTPException(status_code=404, detail="메시지를 찾을 수 없습니다")
        
        # 피드백 업데이트
        message.feedback = request.feedback.value
        message.feedback_comment = request.comment
        db.commit()
        
        return ChatMessageFeedbackResponse(
            message_id=str(message.id),
            feedback=FeedbackType(message.feedback) if message.feedback else FeedbackType.NONE,
            comment=message.feedback_comment,
            created_at=message.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"피드백 업데이트 실패: {str(e)}")


@router.get("/chat/messages/{message_id}/feedback", response_model=ChatMessageFeedbackResponse)
async def get_message_feedback(
    message_id: str,
    db: Session = Depends(get_db)
):
    """채팅 메시지 피드백 조회"""
    try:
        # 메시지 확인
        message = db.query(ChatMessage).filter(ChatMessage.id == int(message_id)).first()
        if not message:
            raise HTTPException(status_code=404, detail="메시지를 찾을 수 없습니다")
        
        return ChatMessageFeedbackResponse(
            message_id=str(message.id),
            feedback=FeedbackType(message.feedback) if message.feedback else FeedbackType.NONE,
            comment=message.feedback_comment,
            created_at=message.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"피드백 조회 실패: {str(e)}")


@router.get("/chat/test", response_model=RAGTestResponse)
async def test_rag_pipeline(db: Session = Depends(get_db)):
    """RAG 파이프라인 테스트"""
    try:
        result = await rag_service.test_rag_pipeline(db=db)
        return RAGTestResponse(**result)
    except Exception as e:
        return RAGTestResponse(
            search_working=False,
            llm_connected=False,
            search_results_count=0,
            test_query="테스트 실패",
            error=str(e)
        )


async def _get_or_create_session(client_id: str, session_id: str = None, db: Session = None):
    """세션 확인 또는 생성"""
    if session_id:
        session = db.query(ChatSession).filter(ChatSession.id == int(session_id)).first()
        if session:
            return session
    
    # 새 세션 생성
    session = ChatSession(
        client_id=client_id,
        title=f"새 대화 {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(session)
    db.commit()
    db.refresh(session)
    
    return session
