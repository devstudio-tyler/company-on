"""
Server-Sent Events (SSE) 서비스
실시간 상태 알림을 위한 SSE 관리
"""
import asyncio
import json
from typing import Dict, Set
from fastapi import Request
from ..schemas.upload_session import UploadProgressResponse
import logging

logger = logging.getLogger(__name__)


class SSEService:
    """SSE 서비스"""
    
    def __init__(self):
        # 클라이언트 연결 관리
        self.connections: Dict[str, Set[Request]] = {}
        # 업로드별 연결 관리
        self.upload_connections: Dict[str, Set[Request]] = {}
    
    async def add_connection(self, client_id: str, request: Request):
        """
        클라이언트 연결 추가
        
        Args:
            client_id: 클라이언트 ID
            request: FastAPI Request 객체
        """
        if client_id not in self.connections:
            self.connections[client_id] = set()
        
        self.connections[client_id].add(request)
        logger.info(f"SSE connection added for client: {client_id}")
    
    async def remove_connection(self, client_id: str, request: Request):
        """
        클라이언트 연결 제거
        
        Args:
            client_id: 클라이언트 ID
            request: FastAPI Request 객체
        """
        if client_id in self.connections:
            self.connections[client_id].discard(request)
            if not self.connections[client_id]:
                del self.connections[client_id]
        
        logger.info(f"SSE connection removed for client: {client_id}")
    
    async def add_upload_connection(self, upload_id: str, request: Request):
        """
        업로드별 연결 추가
        
        Args:
            upload_id: 업로드 ID
            request: FastAPI Request 객체
        """
        if upload_id not in self.upload_connections:
            self.upload_connections[upload_id] = set()
        
        self.upload_connections[upload_id].add(request)
        logger.info(f"SSE connection added for upload: {upload_id}")
    
    async def remove_upload_connection(self, upload_id: str, request: Request):
        """
        업로드별 연결 제거
        
        Args:
            upload_id: 업로드 ID
            request: FastAPI Request 객체
        """
        if upload_id in self.upload_connections:
            self.upload_connections[upload_id].discard(request)
            if not self.upload_connections[upload_id]:
                del self.upload_connections[upload_id]
        
        logger.info(f"SSE connection removed for upload: {upload_id}")
    
    async def send_upload_progress(self, upload_id: str, progress_data: UploadProgressResponse):
        """
        업로드 진행률 전송
        
        Args:
            upload_id: 업로드 ID
            progress_data: 진행률 데이터
        """
        if upload_id not in self.upload_connections:
            return
        
        message = f"data: {progress_data.model_dump_json()}\n\n"
        
        # 연결된 모든 클라이언트에게 전송
        disconnected_clients = set()
        for request in self.upload_connections[upload_id]:
            try:
                await request.send_text(message)
            except Exception as e:
                logger.error(f"Failed to send SSE message: {e}")
                disconnected_clients.add(request)
        
        # 연결이 끊어진 클라이언트 제거
        for request in disconnected_clients:
            await self.remove_upload_connection(upload_id, request)
    
    async def send_general_notification(self, client_id: str, message: str, data: dict = None):
        """
        일반 알림 전송
        
        Args:
            client_id: 클라이언트 ID
            message: 알림 메시지
            data: 추가 데이터
        """
        if client_id not in self.connections:
            return
        
        notification = {
            "type": "notification",
            "message": message,
            "data": data or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        sse_message = f"data: {json.dumps(notification)}\n\n"
        
        # 연결된 모든 클라이언트에게 전송
        disconnected_clients = set()
        for request in self.connections[client_id]:
            try:
                await request.send_text(sse_message)
            except Exception as e:
                logger.error(f"Failed to send SSE notification: {e}")
                disconnected_clients.add(request)
        
        # 연결이 끊어진 클라이언트 제거
        for request in disconnected_clients:
            await self.remove_connection(client_id, request)
    
    async def broadcast_upload_status_change(self, upload_id: str, status: str):
        """
        업로드 상태 변경 브로드캐스트
        
        Args:
            upload_id: 업로드 ID
            status: 새로운 상태
        """
        if upload_id not in self.upload_connections:
            return
        
        status_change = {
            "type": "status_change",
            "upload_id": upload_id,
            "status": status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        message = f"data: {json.dumps(status_change)}\n\n"
        
        # 연결된 모든 클라이언트에게 전송
        disconnected_clients = set()
        for request in self.upload_connections[upload_id]:
            try:
                await request.send_text(message)
            except Exception as e:
                logger.error(f"Failed to send SSE status change: {e}")
                disconnected_clients.add(request)
        
        # 연결이 끊어진 클라이언트 제거
        for request in disconnected_clients:
            await self.remove_upload_connection(upload_id, request)


# 전역 SSE 서비스 인스턴스
sse_service = SSEService()
