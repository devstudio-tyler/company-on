"""
LLM 서비스 - OpenRouter Gemma 3 12B 통합
"""

import os
import json
import logging
from typing import List, Dict, Optional, AsyncGenerator
from openai import AsyncOpenAI
from pydantic import BaseModel
import asyncio

logger = logging.getLogger(__name__)


class LLMConfig(BaseModel):
    """LLM 설정 모델"""
    # 기본값은 경량 모델로 설정 (환경변수로 덮어쓰기 가능)
    model: str = "google/gemma-3-4b-it:free"
    max_tokens: int = 1000
    temperature: float = 0.7
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0


class LLMResponse(BaseModel):
    """LLM 응답 모델"""
    content: str
    usage: Dict[str, int]
    model: str
    finish_reason: str


class LLMService:
    """OpenRouter Gemma 3 12B LLM 서비스"""

    def __init__(self):
        self.config = LLMConfig()
        self.system_prompt = self._get_system_prompt()
        
        # OpenRouter 설정 (OpenAI 호환 API)
        api_key = os.getenv("OPENROUTER_API_KEY")
        base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        
        if not api_key:
            logger.warning("OPENROUTER_API_KEY가 설정되지 않았습니다. LLM 기능이 제한됩니다.")
            self.client = None
        else:
            self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
            
        # 환경변수로 모델 지정 (예: google/gemma-3-12b-it:free 등)
        self.config.model = os.getenv("GEMMA_MODEL", "google/gemma-3-12b-it:free")
        logger.info(f"OpenRouter Gemma 모델 초기화: {self.config.model}")
        
    def _get_system_prompt(self) -> str:
        """RAG용 시스템 프롬프트 생성"""
        return """당신은 Company-on의 AI 어시스턴트입니다. 
        
주요 역할:
1. 사용자의 질문에 대해 제공된 문서 내용을 바탕으로 정확하고 도움이 되는 답변을 제공합니다.
2. 답변할 때는 반드시 참조한 문서의 출처를 명시합니다.
3. 문서에 없는 내용은 추측하지 않고 "제공된 문서에는 해당 정보가 없습니다"라고 명확히 말합니다.
4. 한국어로 자연스럽고 친근하게 답변합니다.

답변 형식:
- 질문에 대한 명확한 답변
- 참조한 문서의 출처 (문서명, 페이지 등)
- 추가로 도움이 필요한 경우 안내

항상 정확하고 신뢰할 수 있는 정보만을 제공하세요."""

    async def generate_response(
        self, 
        user_message: str, 
        context_documents: List[Dict[str, str]] = None,
        conversation_history: List[Dict[str, str]] = None
    ) -> LLMResponse:
        """RAG 기반 응답 생성"""
        if not self.client:
            return LLMResponse(
                content="OpenRouter API 키가 설정되지 않았습니다. 관리자에게 문의하세요.",
                usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                model="none",
                finish_reason="api_key_missing"
            )
        
        try:
            # 컨텍스트 구성
            context_text = self._build_context(context_documents)
            
            # 대화 히스토리 구성
            messages = self._build_messages(
                user_message, 
                context_text, 
                conversation_history
            )
            
            # OpenRouter API 호출 (OpenAI 호환)
            response = await self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                top_p=self.config.top_p,
                frequency_penalty=self.config.frequency_penalty,
                presence_penalty=self.config.presence_penalty
            )
            
            return LLMResponse(
                content=response.choices[0].message.content,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                model=response.model,
                finish_reason=response.choices[0].finish_reason
            )
            
        except Exception as e:
            logger.error(f"LLM 응답 생성 실패: {e}")
            raise

    async def generate_streaming_response(
        self, 
        user_message: str, 
        context_documents: List[Dict[str, str]] = None,
        conversation_history: List[Dict[str, str]] = None
    ) -> AsyncGenerator[str, None]:
        """스트리밍 응답 생성"""
        if not self.client:
            yield "OpenRouter API 키가 설정되지 않았습니다. 관리자에게 문의하세요."
            return
        
        try:
            # 컨텍스트 구성
            context_text = self._build_context(context_documents)
            
            # 대화 히스토리 구성
            messages = self._build_messages(
                user_message, 
                context_text, 
                conversation_history
            )
            
            # OpenRouter 스트리밍 API 호출
            logger.info(f"OpenRouter API 호출 시작: model={self.config.model}")
            logger.info(f"메시지 수: {len(messages)}")
            logger.info(f"메시지 내용: {[msg.get('role', 'unknown') + ': ' + msg.get('content', '')[:100] + '...' for msg in messages]}")
            
            try:
                # 타임아웃 설정 (30초)
                import asyncio
                stream = await asyncio.wait_for(
                    self.client.chat.completions.create(
                        model=self.config.model,
                        messages=messages,
                        max_tokens=self.config.max_tokens,
                        temperature=self.config.temperature,
                        stream=True
                    ),
                    timeout=30.0
                )
                logger.info("OpenRouter API 호출 완료, 스트림 시작")
                
                chunk_count = 0
                async for chunk in stream:
                    chunk_count += 1
                    if chunk.choices and len(chunk.choices) > 0 and chunk.choices[0].delta.content:
                        logger.info(f"스트리밍 청크 #{chunk_count}: {chunk.choices[0].delta.content}")
                        yield chunk.choices[0].delta.content
                    else:
                        logger.debug(f"빈 청크 #{chunk_count}: {chunk}")
                
                logger.info(f"스트리밍 완료: 총 {chunk_count}개 청크 처리")
                
            except asyncio.TimeoutError:
                logger.error("OpenRouter API 호출 타임아웃 (30초)")
                yield "죄송합니다. 응답 생성에 시간이 오래 걸리고 있습니다. 잠시 후 다시 시도해주세요."
                return
            except Exception as api_error:
                logger.error(f"OpenRouter API 호출 중 오류: {api_error}")
                logger.error(f"API 오류 타입: {type(api_error).__name__}")
                logger.error(f"API 오류 상세: {str(api_error)}")
                if hasattr(api_error, 'response'):
                    logger.error(f"API 응답 상태: {api_error.response.status_code if hasattr(api_error.response, 'status_code') else 'unknown'}")
                yield f"API 호출 중 오류가 발생했습니다: {str(api_error)}"
                return
                    
        except Exception as e:
            logger.error(f"LLM 스트리밍 응답 생성 실패: {e}")
            logger.error(f"오류 타입: {type(e).__name__}")
            logger.error(f"오류 상세: {str(e)}")
            raise

    def _build_context(self, context_documents: List[Dict[str, str]]) -> str:
        """검색된 문서들을 컨텍스트로 구성"""
        if not context_documents:
            return "관련 문서가 없습니다."
        
        context_parts = []
        for i, doc in enumerate(context_documents, 1):
            context_parts.append(
                f"[문서 {i}] {doc.get('title', '제목 없음')}\n"
                f"내용: {doc.get('content', '')}\n"
                f"출처: {doc.get('source', '')}\n"
            )
        
        return "\n".join(context_parts)

    def _build_messages(
        self, 
        user_message: str, 
        context_text: str, 
        conversation_history: List[Dict[str, str]] = None
    ) -> List[Dict[str, str]]:
        """메시지 배열 구성"""
        messages = [
            {"role": "system", "content": self.system_prompt}
        ]
        
        # 대화 히스토리 추가
        if conversation_history:
            for msg in conversation_history[-10:]:  # 최근 10개 메시지만
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        # 현재 사용자 메시지와 컨텍스트 추가
        full_user_message = f"""다음 문서들을 참조하여 질문에 답변해주세요:

{context_text}

질문: {user_message}"""
        
        messages.append({
            "role": "user", 
            "content": full_user_message
        })
        
        return messages

    async def test_connection(self) -> bool:
        """OpenRouter API 연결 테스트"""
        if not self.client:
            return False
        
        try:
            response = await self.client.chat.completions.create(
                model=self.config.model,
                messages=[{"role": "user", "content": "안녕하세요"}],
                max_tokens=10
            )
            return response.choices[0].message.content is not None
        except Exception as e:
            logger.error(f"OpenRouter 연결 테스트 실패: {e}")
            return False

    def update_config(self, **kwargs):
        """설정 업데이트"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                logger.info(f"LLM 설정 업데이트: {key}={value}")


# 전역 인스턴스
llm_service = LLMService()
