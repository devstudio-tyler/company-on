from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status, Header
from sqlalchemy.orm import Session
import uuid

from ....database.connection import get_db
from ....services.chat_message_service import ChatMessageService
from ....schemas.chat import (
    ChatMessageCreateRequest,
    ChatMessageResponse,
    ChatMessageListResponse,
    ErrorResponse
)

router = APIRouter(prefix="/chat/sessions/{session_id}/messages", tags=["chat_messages"])

def get_client_id(x_client_id: Optional[str] = Header(None)) -> str:
    """클라이언트 ID 추출 및 검증"""
    if not x_client_id:
        # 클라이언트 ID가 없으면 새로 생성
        return str(uuid.uuid4())
    
    try:
        # UUID 형식 검증
        uuid.UUID(x_client_id)
        return x_client_id
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid client ID format. Must be a valid UUID."
        )

@router.post("", response_model=ChatMessageResponse, status_code=status.HTTP_201_CREATED)
async def create_chat_message(
    session_id: int,
    request: ChatMessageCreateRequest,
    client_id: str = Depends(get_client_id),
    db: Session = Depends(get_db)
):
    """
    새로운 채팅 메시지를 생성합니다.
    
    - **session_id**: 세션 ID
    - **content**: 메시지 내용 (필수)
    - **role**: 메시지 역할 (user, assistant, system)
    - **client_id**: 클라이언트 식별자 (X-Client-ID 헤더 또는 자동 생성)
    """
    chat_service = ChatMessageService(db)
    message = chat_service.create_chat_message(session_id, client_id, request)
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found or access denied"
        )
    
    return message

@router.get("", response_model=ChatMessageListResponse)
async def get_chat_messages(
    session_id: int,
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    client_id: str = Depends(get_client_id),
    db: Session = Depends(get_db)
):
    """
    채팅 메시지 목록을 조회합니다.
    
    - **session_id**: 세션 ID
    - **page**: 페이지 번호 (기본값: 1)
    - **limit**: 페이지당 항목 수 (기본값: 20, 최대: 100)
    - **client_id**: 클라이언트 식별자
    """
    chat_service = ChatMessageService(db)
    messages = chat_service.get_chat_messages(session_id, client_id, page, limit)
    
    if not messages:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found or access denied"
        )
    
    return messages

@router.get("/{message_id}", response_model=ChatMessageResponse)
async def get_chat_message(
    session_id: int,
    message_id: int,
    client_id: str = Depends(get_client_id),
    db: Session = Depends(get_db)
):
    """
    특정 채팅 메시지의 상세 정보를 조회합니다.
    
    - **session_id**: 세션 ID
    - **message_id**: 메시지 ID
    - **client_id**: 클라이언트 식별자
    """
    chat_service = ChatMessageService(db)
    message = chat_service.get_chat_message(message_id, session_id, client_id)
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat message not found or access denied"
        )
    
    return message

@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat_message(
    session_id: int,
    message_id: int,
    client_id: str = Depends(get_client_id),
    db: Session = Depends(get_db)
):
    """
    채팅 메시지를 삭제합니다.
    
    - **session_id**: 세션 ID
    - **message_id**: 메시지 ID
    - **client_id**: 클라이언트 식별자
    """
    chat_service = ChatMessageService(db)
    success = chat_service.delete_chat_message(message_id, session_id, client_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat message not found or access denied"
        )

@router.get("/recent/context", response_model=List[ChatMessageResponse])
async def get_recent_messages_for_context(
    session_id: int,
    limit: int = Query(10, ge=1, le=50, description="최근 메시지 수"),
    client_id: str = Depends(get_client_id),
    db: Session = Depends(get_db)
):
    """
    컨텍스트용 최근 메시지를 조회합니다.
    
    - **session_id**: 세션 ID
    - **limit**: 최근 메시지 수 (기본값: 10, 최대: 50)
    - **client_id**: 클라이언트 식별자
    """
    chat_service = ChatMessageService(db)
    messages = chat_service.get_recent_messages(session_id, client_id, limit)
    
    if not messages:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found or access denied"
        )
    
    return messages
