"""
임베딩 생성 서비스
텍스트를 벡터로 변환하여 임베딩을 생성하는 서비스
"""
import numpy as np
from typing import List, Dict, Any, Optional
import logging
from sentence_transformers import SentenceTransformer
import openai
from openai import OpenAI
import os

logger = logging.getLogger(__name__)

class EmbeddingService:
    """임베딩 생성 서비스"""
    
    def __init__(self, model_name: str = "multilingual-e5-base"):
        """
        임베딩 서비스 초기화
        
        Args:
            model_name: 사용할 임베딩 모델명
        """
        self.model_name = model_name
        self.model = None
        self.openai_client = None
        self.embedding_dimension = 768  # 기본 차원 수
        
        # 모델 초기화
        self._initialize_model()
    
    def _initialize_model(self):
        """임베딩 모델 초기화"""
        try:
            if self.model_name.startswith("openai:"):
                # OpenAI 임베딩 모델
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
                
                self.openai_client = OpenAI(api_key=api_key)
                self.embedding_dimension = 1536  # OpenAI text-embedding-ada-002 차원
                logger.info(f"OpenAI 임베딩 모델 초기화 완료: {self.model_name}")
                
            else:
                # Sentence Transformers 모델
                self.model = SentenceTransformer(self.model_name)
                self.embedding_dimension = self.model.get_sentence_embedding_dimension()
                logger.info(f"Sentence Transformers 모델 초기화 완료: {self.model_name}, 차원: {self.embedding_dimension}")
                
        except Exception as e:
            logger.error(f"임베딩 모델 초기화 실패: {str(e)}")
            raise
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        단일 텍스트에 대한 임베딩 생성
        
        Args:
            text: 임베딩을 생성할 텍스트
            
        Returns:
            임베딩 벡터 (List[float])
        """
        try:
            if not text.strip():
                return [0.0] * self.embedding_dimension
            
            if self.openai_client:
                return self._generate_openai_embedding(text)
            else:
                return self._generate_sentence_transformer_embedding(text)
                
        except Exception as e:
            logger.error(f"임베딩 생성 실패: {str(e)}")
            raise
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        여러 텍스트에 대한 배치 임베딩 생성
        
        Args:
            texts: 임베딩을 생성할 텍스트 리스트
            
        Returns:
            임베딩 벡터 리스트
        """
        try:
            if not texts:
                return []
            
            if self.openai_client:
                return self._generate_openai_embeddings_batch(texts)
            else:
                return self._generate_sentence_transformer_embeddings_batch(texts)
                
        except Exception as e:
            logger.error(f"배치 임베딩 생성 실패: {str(e)}")
            raise
    
    def _generate_openai_embedding(self, text: str) -> List[float]:
        """OpenAI 임베딩 생성"""
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"OpenAI 임베딩 생성 실패: {str(e)}")
            raise
    
    def _generate_openai_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """OpenAI 배치 임베딩 생성"""
        try:
            # OpenAI는 한 번에 최대 2048개까지 처리 가능
            batch_size = 100
            all_embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                
                response = self.openai_client.embeddings.create(
                    model="text-embedding-ada-002",
                    input=batch_texts
                )
                
                batch_embeddings = [data.embedding for data in response.data]
                all_embeddings.extend(batch_embeddings)
            
            return all_embeddings
            
        except Exception as e:
            logger.error(f"OpenAI 배치 임베딩 생성 실패: {str(e)}")
            raise
    
    def _generate_sentence_transformer_embedding(self, text: str) -> List[float]:
        """Sentence Transformers 임베딩 생성"""
        try:
            embedding = self.model.encode(text, convert_to_tensor=False)
            return embedding.tolist()
            
        except Exception as e:
            logger.error(f"Sentence Transformers 임베딩 생성 실패: {str(e)}")
            raise
    
    def _generate_sentence_transformer_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Sentence Transformers 배치 임베딩 생성"""
        try:
            embeddings = self.model.encode(texts, convert_to_tensor=False, batch_size=32)
            return embeddings.tolist()
            
        except Exception as e:
            logger.error(f"Sentence Transformers 배치 임베딩 생성 실패: {str(e)}")
            raise
    
    def normalize_embedding(self, embedding: List[float]) -> List[float]:
        """임베딩 벡터 정규화"""
        try:
            embedding_array = np.array(embedding)
            norm = np.linalg.norm(embedding_array)
            
            if norm == 0:
                return embedding
            
            normalized = embedding_array / norm
            return normalized.tolist()
            
        except Exception as e:
            logger.error(f"임베딩 정규화 실패: {str(e)}")
            return embedding
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """두 임베딩 간의 코사인 유사도 계산"""
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # 코사인 유사도 계산
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"유사도 계산 실패: {str(e)}")
            return 0.0
    
    def get_embedding_info(self) -> Dict[str, Any]:
        """임베딩 모델 정보 반환"""
        return {
            "model_name": self.model_name,
            "embedding_dimension": self.embedding_dimension,
            "provider": "openai" if self.openai_client else "sentence_transformers",
            "supports_batch": True,
            "max_batch_size": 100 if self.openai_client else 1000
        }
    
    def validate_embedding(self, embedding: List[float]) -> bool:
        """임베딩 벡터 유효성 검증"""
        try:
            if not embedding:
                return False
            
            if len(embedding) != self.embedding_dimension:
                return False
            
            # NaN 또는 무한대 값 검사
            embedding_array = np.array(embedding)
            if np.any(np.isnan(embedding_array)) or np.any(np.isinf(embedding_array)):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"임베딩 검증 실패: {str(e)}")
            return False
