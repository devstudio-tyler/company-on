"""
업로드 세션 관리 서비스
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc
from ..models.upload_session import UploadSession
from ..schemas.upload_session import UploadStatus, UploadStatusUpdateRequest
import logging

logger = logging.getLogger(__name__)


class UploadSessionService:
    """업로드 세션 관리 서비스"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_upload_session(
        self,
        upload_id: str,
        filename: str,
        file_size: int,
        content_type: str
    ) -> UploadSession:
        """
        업로드 세션 생성
        
        Args:
            upload_id: 업로드 ID
            filename: 파일명
            file_size: 파일 크기
            content_type: MIME 타입
            
        Returns:
            UploadSession: 생성된 업로드 세션
        """
        session = UploadSession(
            id=upload_id,
            filename=filename,
            file_size=file_size,
            uploaded_size=0,
            content_type=content_type,
            status=UploadStatus.INIT
        )
        
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        
        logger.info(f"Upload session created: {upload_id} - {filename}")
        return session
    
    def get_upload_session(self, upload_id: str) -> Optional[UploadSession]:
        """
        업로드 세션 조회
        
        Args:
            upload_id: 업로드 ID
            
        Returns:
            Optional[UploadSession]: 업로드 세션 또는 None
        """
        return self.db.query(UploadSession).filter(UploadSession.id == upload_id).first()
    
    def get_upload_sessions(
        self,
        page: int = 1,
        limit: int = 20,
        status: Optional[UploadStatus] = None
    ) -> tuple[List[UploadSession], int]:
        """
        업로드 세션 목록 조회
        
        Args:
            page: 페이지 번호
            limit: 페이지당 항목 수
            status: 상태 필터
            
        Returns:
            tuple: (세션 목록, 전체 개수)
        """
        query = self.db.query(UploadSession)
        
        # 상태 필터
        if status:
            query = query.filter(UploadSession.status == status)
        
        # 전체 개수
        total = query.count()
        
        # 페이지네이션
        sessions = query.order_by(desc(UploadSession.created_at)).offset((page - 1) * limit).limit(limit).all()
        
        return sessions, total
    
    def update_upload_status(
        self,
        upload_id: str,
        status: UploadStatus,
        uploaded_size: Optional[int] = None,
        document_id: Optional[int] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """
        업로드 상태 업데이트
        
        Args:
            upload_id: 업로드 ID
            status: 새로운 상태
            uploaded_size: 업로드된 크기
            document_id: 연결된 문서 ID
            error_message: 에러 메시지
            
        Returns:
            bool: 업데이트 성공 여부
        """
        session = self.get_upload_session(upload_id)
        if not session:
            return False
        
        session.status = status
        session.updated_at = datetime.utcnow()
        
        if uploaded_size is not None:
            session.uploaded_size = uploaded_size
        
        if document_id is not None:
            session.document_id = document_id
        
        if error_message is not None:
            session.error_message = error_message
        
        self.db.commit()
        logger.info(f"Upload session status updated: {upload_id} -> {status}")
        return True
    
    def update_upload_progress(
        self,
        upload_id: str,
        uploaded_size: int
    ) -> bool:
        """
        업로드 진행률 업데이트
        
        Args:
            upload_id: 업로드 ID
            uploaded_size: 업로드된 크기
            
        Returns:
            bool: 업데이트 성공 여부
        """
        session = self.get_upload_session(upload_id)
        if not session:
            return False
        
        session.uploaded_size = uploaded_size
        session.status = UploadStatus.UPLOADING
        session.updated_at = datetime.utcnow()
        
        self.db.commit()
        return True
    
    def complete_upload(
        self,
        upload_id: str,
        document_id: int
    ) -> bool:
        """
        업로드 완료 처리
        
        Args:
            upload_id: 업로드 ID
            document_id: 생성된 문서 ID
            
        Returns:
            bool: 완료 처리 성공 여부
        """
        return self.update_upload_status(
            upload_id=upload_id,
            status=UploadStatus.PENDING,
            uploaded_size=None,  # 전체 크기로 설정
            document_id=document_id
        )
    
    def fail_upload(
        self,
        upload_id: str,
        error_message: str
    ) -> bool:
        """
        업로드 실패 처리
        
        Args:
            upload_id: 업로드 ID
            error_message: 에러 메시지
            
        Returns:
            bool: 실패 처리 성공 여부
        """
        return self.update_upload_status(
            upload_id=upload_id,
            status=UploadStatus.FAILED,
            error_message=error_message
        )
    
    def delete_upload_session(self, upload_id: str) -> bool:
        """
        업로드 세션 삭제
        
        Args:
            upload_id: 업로드 ID
            
        Returns:
            bool: 삭제 성공 여부
        """
        session = self.get_upload_session(upload_id)
        if not session:
            return False
        
        self.db.delete(session)
        self.db.commit()
        
        logger.info(f"Upload session deleted: {upload_id}")
        return True
