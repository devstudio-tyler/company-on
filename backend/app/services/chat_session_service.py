from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from datetime import datetime
import uuid

from ..models.chat import ChatSession, ChatMessage
from ..schemas.chat import (
    ChatSessionCreateRequest, 
    ChatSessionUpdateRequest, 
    ChatSessionResponse,
    ChatSessionListResponse,
    ChatSessionSearchRequest,
    ChatSessionStatus
)

class ChatSessionService:
    """채팅 세션 관리 서비스"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_chat_session(
        self, 
        client_id: str, 
        request: ChatSessionCreateRequest
    ) -> ChatSessionResponse:
        """새로운 채팅 세션 생성"""
        
        # 새 세션 생성
        new_session = ChatSession(
            client_id=client_id,
            title=request.title,
            summary=request.description,  # description을 summary로 매핑
            tags=request.tags or [],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.db.add(new_session)
        self.db.commit()
        self.db.refresh(new_session)
        
        return self._session_to_response(new_session)
    
    def get_chat_session(self, session_id: int, client_id: str) -> Optional[ChatSessionResponse]:
        """특정 채팅 세션 조회"""
        
        session = self.db.query(ChatSession).filter(
            and_(
                ChatSession.id == session_id,
                ChatSession.client_id == client_id,
            )
        ).first()
        
        if not session:
            return None
            
        return self._session_to_response(session)
    
    def get_chat_sessions(
        self, 
        client_id: str, 
        search_request: ChatSessionSearchRequest
    ) -> ChatSessionListResponse:
        """채팅 세션 목록 조회 (검색/필터링 포함)"""
        
        # 기본 쿼리
        query = self.db.query(ChatSession).filter(
            ChatSession.client_id == client_id
        )
        
        # 검색 쿼리 적용
        if search_request.query:
            search_filter = or_(
                ChatSession.title.ilike(f"%{search_request.query}%"),
                ChatSession.summary.ilike(f"%{search_request.query}%"),
                ChatSession.tags.contains([search_request.query])
            )
            query = query.filter(search_filter)
        
        # 태그 필터 적용
        if search_request.tags:
            for tag in search_request.tags:
                query = query.filter(ChatSession.tags.contains([tag]))
        
        # 상태 필터는 모델에 없으므로 제거
        
        # 전체 개수 조회
        total = query.count()
        
        # 페이지네이션 적용
        offset = (search_request.page - 1) * search_request.size
        sessions = query.order_by(desc(ChatSession.updated_at)).offset(offset).limit(search_request.size).all()
        
        # 응답 변환
        session_responses = [self._session_to_response(session) for session in sessions]
        
        return ChatSessionListResponse(
            sessions=session_responses,
            total=total,
            page=search_request.page,
            size=search_request.size
        )
    
    def update_chat_session(
        self, 
        session_id: int, 
        client_id: str, 
        request: ChatSessionUpdateRequest
    ) -> Optional[ChatSessionResponse]:
        """채팅 세션 수정"""
        
        session = self.db.query(ChatSession).filter(
            and_(
                ChatSession.id == session_id,
                ChatSession.client_id == client_id,
            )
        ).first()
        
        if not session:
            return None
        
        # 업데이트할 필드만 수정
        if request.title is not None:
            session.title = request.title
        if request.description is not None:
            session.description = request.description
        if request.tags is not None:
            session.tags = request.tags
        if request.is_pinned is not None:
            session.is_pinned = 'true' if request.is_pinned else 'false'
        
        session.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(session)
        
        return self._session_to_response(session)
    
    def delete_chat_session(self, session_id: int, client_id: str) -> bool:
        """채팅 세션 삭제 (소프트 삭제)"""
        
        session = self.db.query(ChatSession).filter(
            and_(
                ChatSession.id == session_id,
                ChatSession.client_id == client_id,
            )
        ).first()
        
        if not session:
            return False
        
        # 실제 삭제 (모델에 status 필드가 없음)
        self.db.delete(session)
        session.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        return True
    
    def get_session_stats(self, client_id: str) -> dict:
        """클라이언트의 세션 통계 조회"""
        
        # 상태 필드가 없으므로 전체 세션 수만 반환
        total_count = self.db.query(ChatSession).filter(
            ChatSession.client_id == client_id
        ).count()
        
        return {
            "active": total_count
        }
    
    def _session_to_response(self, session: ChatSession) -> ChatSessionResponse:
        """ChatSession 모델을 ChatSessionResponse로 변환"""
        
        # 메시지 수 조회
        message_count = self.db.query(ChatMessage).filter(
            ChatMessage.session_id == session.id
        ).count()
        
        # 마지막 메시지 시간 조회
        last_message = self.db.query(ChatMessage).filter(
            ChatMessage.session_id == session.id
        ).order_by(desc(ChatMessage.created_at)).first()
        
        last_message_at = last_message.created_at if last_message else None
        
        return ChatSessionResponse(
            session_id=str(session.id),
            client_id=str(session.client_id),
            title=session.title or "",
            description=session.description,
            tags=session.tags or [],
            is_pinned=session.is_pinned == 'true',
            message_count=message_count,
            created_at=session.created_at,
            updated_at=session.updated_at
        )
