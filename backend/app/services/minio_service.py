"""
MinIO 파일 저장소 서비스
"""
import os
import uuid
from datetime import datetime, timedelta
from typing import Optional, BinaryIO
from minio import Minio
from minio.error import S3Error
import logging

logger = logging.getLogger(__name__)


class MinIOService:
    """MinIO 파일 저장소 서비스"""
    
    def __init__(self):
        self.client = Minio(
            endpoint=os.getenv("MINIO_ENDPOINT", "localhost:9000"),
            access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
            secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin123"),
            secure=False  # 개발 환경에서는 HTTP 사용
        )
        self.bucket_name = "company-on-documents"
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """버킷이 존재하는지 확인하고 없으면 생성"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Created bucket: {self.bucket_name}")
        except S3Error as e:
            logger.error(f"Failed to create bucket: {e}")
            raise
    
    def generate_upload_url(self, filename: str, expires_minutes: int = 60) -> tuple[str, str]:
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
            upload_url = self.client.presigned_put_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                expires=timedelta(minutes=expires_minutes)
            )
            return upload_id, upload_url
        except S3Error as e:
            logger.error(f"Failed to generate upload URL: {e}")
            raise
    
    def get_file_url(self, file_path: str, expires_minutes: int = 60) -> str:
        """
        파일 다운로드를 위한 사전 서명된 URL 생성
        
        Args:
            file_path: 파일 경로
            expires_minutes: URL 만료 시간 (분)
            
        Returns:
            str: 다운로드 URL
        """
        try:
            download_url = self.client.presigned_get_object(
                bucket_name=self.bucket_name,
                object_name=file_path,
                expires=timedelta(minutes=expires_minutes)
            )
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
