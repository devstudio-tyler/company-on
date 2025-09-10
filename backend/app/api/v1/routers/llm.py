from fastapi import APIRouter, HTTPException
from app.services.llm_service import llm_service

router = APIRouter(prefix="/llm", tags=["llm"])

@router.get("/ping")
async def ping_llm():
    ok = await llm_service.test_connection()
    if not ok:
        raise HTTPException(status_code=503, detail="LLM 연결 실패")
    return {"status": "ok"}
