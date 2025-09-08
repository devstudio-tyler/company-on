"""
SSE + Redis Pub/Sub 서비스
Celery 워커에서 Redis를 통해 SSE 서비스로 메시지 전달
"""
import json
import redis
import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class SSERedisService:
    """SSE + Redis Pub/Sub 서비스"""
    
    def __init__(self):
        self.redis_client = redis.Redis.from_url(
            os.getenv("REDIS_URL", "redis://redis:6379/0")
        )
        self.channel_prefix = "sse_notifications"
    
    def publish_upload_status_change(self, upload_id: str, status: str, message: str = ""):
        """
        업로드 상태 변경 알림 발행 (Celery 워커에서 호출)
        
        Args:
            upload_id: 업로드 ID
            status: 새로운 상태
            message: 추가 메시지
        """
        try:
            notification = {
                "type": "upload_status_change",
                "upload_id": upload_id,
                "status": status,
                "message": message,
                "timestamp": self._get_timestamp()
            }
            
            channel = f"{self.channel_prefix}:upload:{upload_id}"
            self.redis_client.publish(channel, json.dumps(notification))
            
            logger.info(f"Published SSE notification: {upload_id} -> {status}")
            
        except Exception as e:
            logger.error(f"Failed to publish SSE notification: {e}")
    
    def publish_processing_progress(self, upload_id: str, progress: int, total: int, message: str = ""):
        """
        처리 진행률 알림 발행 (Celery 워커에서 호출)
        
        Args:
            upload_id: 업로드 ID
            progress: 현재 진행률
            total: 전체 진행률
            message: 추가 메시지
        """
        try:
            notification = {
                "type": "processing_progress",
                "upload_id": upload_id,
                "progress": progress,
                "total": total,
                "message": message,
                "timestamp": self._get_timestamp()
            }
            
            channel = f"{self.channel_prefix}:upload:{upload_id}"
            self.redis_client.publish(channel, json.dumps(notification))
            
            logger.info(f"Published progress notification: {upload_id} -> {progress}/{total}")
            
        except Exception as e:
            logger.error(f"Failed to publish progress notification: {e}")
    
    def publish_general_notification(self, client_id: str, message: str, data: Dict[str, Any] = None):
        """
        일반 알림 발행 (Celery 워커에서 호출)
        
        Args:
            client_id: 클라이언트 ID
            message: 알림 메시지
            data: 추가 데이터
        """
        try:
            notification = {
                "type": "general_notification",
                "client_id": client_id,
                "message": message,
                "data": data or {},
                "timestamp": self._get_timestamp()
            }
            
            channel = f"{self.channel_prefix}:client:{client_id}"
            self.redis_client.publish(channel, json.dumps(notification))
            
            logger.info(f"Published general notification: {client_id}")
            
        except Exception as e:
            logger.error(f"Failed to publish general notification: {e}")
    
    def _get_timestamp(self) -> str:
        """현재 시간을 ISO 형식으로 반환"""
        from datetime import datetime
        return datetime.utcnow().isoformat()


# 전역 인스턴스
sse_redis_service = SSERedisService()

