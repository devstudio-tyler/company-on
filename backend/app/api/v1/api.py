"""
API v1 라우터 통합
"""
from fastapi import APIRouter
from .routers import documents

api_router = APIRouter(prefix="/api/v1")

# 문서 관리 라우터 등록
api_router.include_router(documents.router)
