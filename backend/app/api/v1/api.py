"""
API v1 라우터 통합
"""
from fastapi import APIRouter
from .routers import documents, upload_status

api_router = APIRouter(prefix="/api/v1")

# 문서 관리 라우터 등록
api_router.include_router(documents.router)

# 업로드 상태 추적 라우터 등록
api_router.include_router(upload_status.router)
