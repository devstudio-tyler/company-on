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
    RAGTestResponse
)
from ....models.chat import ChatSession, ChatMessage

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
            id=str(uuid.uuid4()),
            session_id=session.id,
            client_id=request.client_id,
            content=request.content,
            is_user=True,
            created_at=datetime.utcnow()
        )
        db.add(user_message)
        db.commit()
        
        # RAG 응답 생성
        rag_request = rag_service.RAGRequest(
            query=request.content,
            client_id=request.client_id,
            session_id=session.id,
            max_results=request.max_results,
            include_history=request.include_history
        )
        
        rag_response = await rag_service.generate_answer(rag_request, db)
        
        # AI 응답 메시지 저장
        ai_message = ChatMessage(
            id=str(uuid.uuid4()),
            session_id=session.id,
            client_id=request.client_id,
            content=rag_response.answer,
            is_user=False,
            created_at=datetime.utcnow()
        )
        db.add(ai_message)
        
        # 세션 업데이트
        session.updated_at = datetime.utcnow()
        db.commit()
        
        return ChatMessageResponse(
            message_id=ai_message.id,
            content=rag_response.answer,
            is_user=False,
            session_id=session.id,
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
            id=str(uuid.uuid4()),
            session_id=session.id,
            client_id=request.client_id,
            content=request.content,
            is_user=True,
            created_at=datetime.utcnow()
        )
        db.add(user_message)
        db.commit()
        
        # RAG 스트리밍 응답 생성
        rag_request = rag_service.RAGRequest(
            query=request.content,
            client_id=request.client_id,
            session_id=session.id,
            max_results=request.max_results,
            include_history=request.include_history
        )
        
        async def generate_stream():
            try:
                # 스트리밍 응답 생성
                full_response = ""
                async for chunk in rag_service.generate_streaming_answer(rag_request, db):
                    full_response += chunk
                    yield f"data: {json.dumps({'content': chunk, 'type': 'chunk'})}\n\n"
                
                # 완료된 응답 저장
                ai_message = ChatMessage(
                    id=str(uuid.uuid4()),
                    session_id=session.id,
                    client_id=request.client_id,
                    content=full_response,
                    is_user=False,
                    created_at=datetime.utcnow()
                )
                db.add(ai_message)
                
                # 세션 업데이트
                session.updated_at = datetime.utcnow()
                db.commit()
                
                # 완료 신호
                yield f"data: {json.dumps({'type': 'complete', 'message_id': ai_message.id})}\n\n"
                
            except Exception as e:
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
            id=str(uuid.uuid4()),
            client_id=request.client_id,
            title=request.title or f"새 대화 {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(session)
        db.commit()
        db.refresh(session)
        
        return ChatSessionResponse(
            session_id=session.id,
            client_id=session.client_id,
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
                session_id=session.id,
                client_id=session.client_id,
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
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at.asc()).offset(offset).limit(size).all()
        
        total = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).count()
        
        message_responses = []
        for message in messages:
            message_responses.append(ChatMessageResponse(
                message_id=message.id,
                content=message.content,
                is_user=message.is_user,
                session_id=message.session_id,
                client_id=message.client_id,
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
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="채팅 세션을 찾을 수 없습니다")
        
        # 관련 메시지 삭제
        db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
        
        # 세션 삭제
        db.delete(session)
        db.commit()
        
        return {"message": "채팅 세션이 삭제되었습니다"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"채팅 세션 삭제 실패: {str(e)}")


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
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if session:
            return session
    
    # 새 세션 생성
    session = ChatSession(
        id=str(uuid.uuid4()),
        client_id=client_id,
        title=f"새 대화 {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(session)
    db.commit()
    db.refresh(session)
    
    return session
