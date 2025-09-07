from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, Header
from sqlalchemy.orm import Session
import uuid

from ....database.connection import get_db
from ....services.chat_session_service import ChatSessionService
from ....schemas.chat import (
    ChatSessionCreateRequest,
    ChatSessionUpdateRequest,
    ChatSessionResponse,
    ChatSessionListResponse,
    ChatSessionSearchRequest,
    ChatSessionStatus,
    ErrorResponse
)

router = APIRouter(prefix="/chat/sessions", tags=["chat_sessions"])

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

@router.post("", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_chat_session(
    request: ChatSessionCreateRequest,
    client_id: str = Depends(get_client_id),
    db: Session = Depends(get_db)
):
    """
    새로운 채팅 세션을 생성합니다.
    
    - **title**: 세션 제목 (필수)
    - **description**: 세션 설명 (선택)
    - **tags**: 태그 목록 (선택)
    - **client_id**: 클라이언트 식별자 (X-Client-ID 헤더 또는 자동 생성)
    """
    chat_service = ChatSessionService(db)
    session = chat_service.create_chat_session(client_id, request)
    
    return session

@router.get("", response_model=ChatSessionListResponse)
async def get_chat_sessions(
    query: Optional[str] = Query(None, description="검색 쿼리 (제목, 설명, 태그)"),
    tags: Optional[str] = Query(None, description="태그 필터 (쉼표로 구분)"),
    status_filter: Optional[ChatSessionStatus] = Query(None, alias="status", description="상태 필터"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    client_id: str = Depends(get_client_id),
    db: Session = Depends(get_db)
):
    """
    채팅 세션 목록을 조회합니다.
    
    - **query**: 제목, 설명, 태그에서 검색
    - **tags**: 특정 태그가 포함된 세션만 조회 (쉼표로 구분)
    - **status**: 세션 상태별 필터링
    - **page**: 페이지 번호 (기본값: 1)
    - **limit**: 페이지당 항목 수 (기본값: 20, 최대: 100)
    """
    # 태그 문자열을 리스트로 변환
    tag_list = None
    if tags:
        tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
    
    search_request = ChatSessionSearchRequest(
        query=query,
        tags=tag_list,
        status=status_filter,
        page=page,
        limit=limit
    )
    
    chat_service = ChatSessionService(db)
    sessions = chat_service.get_chat_sessions(client_id, search_request)
    
    return sessions

@router.get("/{session_id}", response_model=ChatSessionResponse)
async def get_chat_session(
    session_id: int,
    client_id: str = Depends(get_client_id),
    db: Session = Depends(get_db)
):
    """
    특정 채팅 세션의 상세 정보를 조회합니다.
    
    - **session_id**: 세션 ID
    - **client_id**: 클라이언트 식별자
    """
    chat_service = ChatSessionService(db)
    session = chat_service.get_chat_session(session_id, client_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    return session

@router.put("/{session_id}", response_model=ChatSessionResponse)
async def update_chat_session(
    session_id: int,
    request: ChatSessionUpdateRequest,
    client_id: str = Depends(get_client_id),
    db: Session = Depends(get_db)
):
    """
    채팅 세션 정보를 수정합니다.
    
    - **session_id**: 세션 ID
    - **title**: 세션 제목 (선택)
    - **description**: 세션 설명 (선택)
    - **tags**: 태그 목록 (선택)
    - **status**: 세션 상태 (선택)
    """
    chat_service = ChatSessionService(db)
    session = chat_service.update_chat_session(session_id, client_id, request)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    return session

@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat_session(
    session_id: int,
    client_id: str = Depends(get_client_id),
    db: Session = Depends(get_db)
):
    """
    채팅 세션을 삭제합니다. (소프트 삭제)
    
    - **session_id**: 세션 ID
    - **client_id**: 클라이언트 식별자
    """
    chat_service = ChatSessionService(db)
    success = chat_service.delete_chat_session(session_id, client_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )

@router.get("/stats/summary")
async def get_chat_session_stats(
    client_id: str = Depends(get_client_id),
    db: Session = Depends(get_db)
):
    """
    클라이언트의 채팅 세션 통계를 조회합니다.
    
    - **client_id**: 클라이언트 식별자
    """
    chat_service = ChatSessionService(db)
    stats = chat_service.get_session_stats(client_id)
    
    return {
        "client_id": client_id,
        "session_counts": stats,
        "total_sessions": sum(stats.values())
    }

@router.post("/search", response_model=ChatSessionListResponse)
async def search_chat_sessions(
    search_request: ChatSessionSearchRequest,
    client_id: str = Depends(get_client_id),
    db: Session = Depends(get_db)
):
    """
    고급 검색을 통해 채팅 세션을 조회합니다.
    
    - **query**: 검색 쿼리
    - **tags**: 태그 필터
    - **status**: 상태 필터
    - **page**: 페이지 번호
    - **limit**: 페이지당 항목 수
    """
    chat_service = ChatSessionService(db)
    sessions = chat_service.get_chat_sessions(client_id, search_request)
    
    return sessions
