"""
MinIO 파일 저장소 서비스
"""
import os
import uuid
from datetime import datetime, timedelta
from typing import Optional, BinaryIO
from minio import Minio
from minio.error import S3Error
import time
import socket
import logging

logger = logging.getLogger(__name__)


class MinIOService:
    """MinIO 파일 저장소 서비스"""
    
    def __init__(self):
        self.client = Minio(
            endpoint=os.getenv("MINIO_ENDPOINT", "localhost:9000"),
            access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
            secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
            secure=False  # 개발 환경에서는 HTTP 사용
        )
        self.bucket_name = "company-on-documents"
        # 초기 부팅 시점에 MinIO DNS/서비스가 준비되지 않을 수 있으므로 재시도
        self._ensure_bucket_exists_with_retry()
    
    def _ensure_bucket_exists(self):
        """버킷이 존재하는지 확인하고 없으면 생성"""
        if not self.client.bucket_exists(self.bucket_name):
            self.client.make_bucket(self.bucket_name)
            logger.info(f"Created bucket: {self.bucket_name}")

    def _ensure_bucket_exists_with_retry(self, retries: int = 10, delay_seconds: float = 3.0):
        """MinIO 초기 연결 재시도. 실패해도 앱 부팅은 계속되게 함."""
        for attempt in range(1, retries + 1):
            try:
                self._ensure_bucket_exists()
                return
            except (S3Error, socket.gaierror, ConnectionError, Exception) as e:  # 광범위하게 재시도
                logger.warning(
                    f"MinIO bucket ensure attempt {attempt}/{retries} failed: {e}. Retrying in {delay_seconds}s"
                )
                time.sleep(delay_seconds)
        # 재시도 후에도 실패 시, 치명적으로 중단하지 않고 경고만 남김. 런타임 시도 시 다시 시도됨
        logger.error("MinIO bucket ensure failed after retries. Continuing without raising to keep API up.")
    
    def _rewrite_to_public_url(self, url: str) -> str:
        """컨테이너 내부 호스트(minio)로 생성된 URL을 브라우저 접근 가능한 퍼블릭 URL로 변환"""
        public_base = os.getenv("MINIO_PUBLIC_BASE_URL")  # 예: http://localhost:9000
        if not public_base:
            return url
        try:
            from urllib.parse import urlparse, urlunparse
            parsed = urlparse(url)
            public_parsed = urlparse(public_base)
            replaced = parsed._replace(scheme=public_parsed.scheme or parsed.scheme,
                                       netloc=public_parsed.netloc or parsed.netloc)
            return urlunparse(replaced)
        except Exception:
            return url

    def generate_upload_url(self, filename: str, expires_minutes: int = 30) -> tuple[str, str]:
        """
        파일 업로드를 위한 사전 서명된 URL 생성
        
        Args:
            filename: 업로드할 파일명
            expires_minutes: URL 만료 시간 (분)
            
        Returns:
            tuple: (upload_id, upload_url)
        """
        upload_id = str(uuid.uuid4())
        object_name = f"uploads/{upload_id}/{filename}"
        
        try:
            # 런타임에서도 버킷 보장 시도 (초기화 단계 실패 대비)
            self._ensure_bucket_exists_with_retry(retries=1, delay_seconds=0.5)
            upload_url = self.client.presigned_put_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                expires=timedelta(minutes=expires_minutes)
            )
            upload_url = self._rewrite_to_public_url(upload_url)
            return upload_id, upload_url
        except S3Error as e:
            logger.error(f"Failed to generate upload URL: {e}")
            raise
    
    def get_file_url(self, file_path: str, expires_minutes: int = 30) -> str:
        """
        파일 다운로드를 위한 사전 서명된 URL 생성
        
        Args:
            file_path: 파일 경로
            expires_minutes: URL 만료 시간 (분)
            
        Returns:
            str: 다운로드 URL
        """
        try:
            self._ensure_bucket_exists_with_retry(retries=1, delay_seconds=0.5)
            # 내부 MinIO 클라이언트로 presigned URL 생성
            download_url = self.client.presigned_get_object(
                bucket_name=self.bucket_name,
                object_name=file_path,
                expires=timedelta(minutes=expires_minutes)
            )
            
            # URL을 퍼블릭 엔드포인트로 변환
            public_base = os.getenv("MINIO_PUBLIC_BASE_URL", "http://localhost:9000")
            if public_base and "minio:9000" in download_url:
                download_url = download_url.replace("minio:9000", public_base.replace("http://", "").replace("https://", ""))
            
            return download_url
        except S3Error as e:
            logger.error(f"Failed to generate download URL: {e}")
            raise
    
    def upload_file(self, file_data: BinaryIO, file_path: str, content_type: str) -> bool:
        """
        파일 업로드
        
        Args:
            file_data: 업로드할 파일 데이터
            file_path: 저장할 파일 경로
            content_type: 파일 MIME 타입
            
        Returns:
            bool: 업로드 성공 여부
        """
        try:
            self._ensure_bucket_exists_with_retry(retries=1, delay_seconds=0.5)
            # 파일 크기 계산
            file_data.seek(0, 2)  # 파일 끝으로 이동
            file_size = file_data.tell()
            file_data.seek(0)  # 파일 시작으로 이동
            
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=file_path,
                data=file_data,
                length=file_size,
                content_type=content_type
            )
            logger.info(f"File uploaded successfully: {file_path}")
            return True
        except S3Error as e:
            logger.error(f"Failed to upload file: {e}")
            return False
    
    def download_file(self, file_path: str) -> Optional[bytes]:
        """
        파일 다운로드
        
        Args:
            file_path: 다운로드할 파일 경로
            
        Returns:
            Optional[bytes]: 파일 데이터 또는 None
        """
        try:
            self._ensure_bucket_exists_with_retry(retries=1, delay_seconds=0.5)
            response = self.client.get_object(
                bucket_name=self.bucket_name,
                object_name=file_path
            )
            return response.read()
        except S3Error as e:
            logger.error(f"Failed to download file: {e}")
            return None
    
    def delete_file(self, file_path: str) -> bool:
        """
        파일 삭제
        
        Args:
            file_path: 삭제할 파일 경로
            
        Returns:
            bool: 삭제 성공 여부
        """
        try:
            self._ensure_bucket_exists_with_retry(retries=1, delay_seconds=0.5)
            self.client.remove_object(
                bucket_name=self.bucket_name,
                object_name=file_path
            )
            logger.info(f"File deleted successfully: {file_path}")
            return True
        except S3Error as e:
            logger.error(f"Failed to delete file: {e}")
            return False
    
    def file_exists(self, file_path: str) -> bool:
        """
        파일 존재 여부 확인
        
        Args:
            file_path: 확인할 파일 경로
            
        Returns:
            bool: 파일 존재 여부
        """
        try:
            self.client.stat_object(
                bucket_name=self.bucket_name,
                object_name=file_path
            )
            return True
        except S3Error:
            return False


# 전역 인스턴스
minio_service = MinIOService()