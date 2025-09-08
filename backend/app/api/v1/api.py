"""
API v1 라우터 통합
"""
from fastapi import APIRouter
from .routers import documents, upload_status, chat_sessions, chat_messages, document_processing, search, chat

api_router = APIRouter(prefix="/api/v1")

# 문서 관리 라우터 등록
api_router.include_router(documents.router)

# 업로드 상태 추적 라우터 등록
api_router.include_router(upload_status.router)

# 채팅 세션 라우터 등록
api_router.include_router(chat_sessions.router)

# 채팅 메시지 라우터 등록
api_router.include_router(chat_messages.router)

# 문서 처리 파이프라인 라우터 등록
api_router.include_router(document_processing.router)

# 검색 라우터 등록
api_router.include_router(search.router)

# 채팅 라우터 등록 (RAG 통합)
api_router.include_router(chat.router)
