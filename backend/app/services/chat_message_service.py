from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from datetime import datetime

from ..models.chat import ChatSession, ChatMessage
from ..schemas.chat import (
    ChatMessageCreateRequest,
    ChatMessageResponse,
    ChatMessageListResponse,
    ChatMessageRole
)

class ChatMessageService:
    """채팅 메시지 관리 서비스"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_chat_message(
        self, 
        session_id: int, 
        client_id: str, 
        request: ChatMessageCreateRequest
    ) -> Optional[ChatMessageResponse]:
        """새로운 채팅 메시지 생성"""
        
        # 세션 존재 및 권한 확인
        session = self.db.query(ChatSession).filter(
            and_(
                ChatSession.id == session_id,
                ChatSession.client_id == client_id,
            )
        ).first()
        
        if not session:
            return None
        
        # 새 메시지 생성
        new_message = ChatMessage(
            session_id=session_id,
            content=request.content,
            role=request.role.value,
            created_at=datetime.utcnow()
        )
        
        self.db.add(new_message)
        
        # 세션의 updated_at 업데이트
        session.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(new_message)
        
        return self._message_to_response(new_message)
    
    def get_chat_messages(
        self, 
        session_id: int, 
        client_id: str, 
        page: int = 1, 
        limit: int = 20
    ) -> Optional[ChatMessageListResponse]:
        """채팅 메시지 목록 조회"""
        
        # 세션 존재 및 권한 확인
        session = self.db.query(ChatSession).filter(
            and_(
                ChatSession.id == session_id,
                ChatSession.client_id == client_id,
            )
        ).first()
        
        if not session:
            return None
        
        # 메시지 조회
        query = self.db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        )
        
        # 전체 개수 조회
        total = query.count()
        
        # 페이지네이션 적용
        offset = (page - 1) * limit
        messages = query.order_by(ChatMessage.created_at).offset(offset).limit(limit).all()
        
        # 응답 변환
        message_responses = [self._message_to_response(message) for message in messages]
        
        return ChatMessageListResponse(
            messages=message_responses,
            total=total,
            page=page,
            size=limit
        )
    
    def get_chat_message(
        self, 
        message_id: int, 
        session_id: int, 
        client_id: str
    ) -> Optional[ChatMessageResponse]:
        """특정 채팅 메시지 조회"""
        
        # 세션 존재 및 권한 확인
        session = self.db.query(ChatSession).filter(
            and_(
                ChatSession.id == session_id,
                ChatSession.client_id == client_id,
            )
        ).first()
        
        if not session:
            return None
        
        # 메시지 조회
        message = self.db.query(ChatMessage).filter(
            and_(
                ChatMessage.id == message_id,
                ChatMessage.session_id == session_id
            )
        ).first()
        
        if not message:
            return None
            
        return self._message_to_response(message)
    
    def delete_chat_message(
        self, 
        message_id: int, 
        session_id: int, 
        client_id: str
    ) -> bool:
        """채팅 메시지 삭제"""
        
        # 세션 존재 및 권한 확인
        session = self.db.query(ChatSession).filter(
            and_(
                ChatSession.id == session_id,
                ChatSession.client_id == client_id,
            )
        ).first()
        
        if not session:
            return False
        
        # 메시지 삭제
        message = self.db.query(ChatMessage).filter(
            and_(
                ChatMessage.id == message_id,
                ChatMessage.session_id == session_id
            )
        ).first()
        
        if not message:
            return False
        
        self.db.delete(message)
        self.db.commit()
        
        return True
    
    def get_recent_messages(
        self, 
        session_id: int, 
        client_id: str, 
        limit: int = 10
    ) -> List[ChatMessageResponse]:
        """최근 메시지 조회 (컨텍스트용)"""
        
        # 세션 존재 및 권한 확인
        session = self.db.query(ChatSession).filter(
            and_(
                ChatSession.id == session_id,
                ChatSession.client_id == client_id,
            )
        ).first()
        
        if not session:
            return []
        
        # 최근 메시지 조회
        messages = self.db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(desc(ChatMessage.created_at)).limit(limit).all()
        
        # 시간순으로 정렬 (오래된 것부터)
        messages.reverse()
        
        return [self._message_to_response(message) for message in messages]
    
    def _message_to_response(self, message: ChatMessage) -> ChatMessageResponse:
        """ChatMessage 모델을 ChatMessageResponse로 변환"""
        
        return ChatMessageResponse(
            message_id=str(message.id),
            content=message.content,
            is_user=(message.role == 'user'),
            session_id=str(message.session_id),
            client_id="",  # 메시지 저장 시에는 client_id 정보가 없음
            sources=message.sources or [],  # 데이터베이스에서 sources 읽기
            usage=message.usage or {},    # 데이터베이스에서 usage 읽기
            model=message.model or "",    # 데이터베이스에서 model 읽기
            created_at=message.created_at
        )
