from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.v1.api import api_router
from .services.sse_service import sse_service

app = FastAPI(
    title="Company-on API",
    description="Company-on RAG-based AI chatbot for internal document search",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 등록
app.include_router(api_router)

# SSE Redis 구독 시작
@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 실행"""
    await sse_service.start_redis_subscription()

@app.get("/")
async def root():
    return {"message": "Company-on API is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Company-on service is running"}

