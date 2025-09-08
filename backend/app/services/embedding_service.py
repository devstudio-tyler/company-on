"""
임베딩 생성 서비스
텍스트를 벡터로 변환하여 임베딩을 생성하는 서비스
"""
import numpy as np
from typing import List, Dict, Any, Optional
import logging
from sentence_transformers import SentenceTransformer
import os

logger = logging.getLogger(__name__)

class EmbeddingService:
    """임베딩 생성 서비스"""
    
    def __init__(self, model_name: str = "intfloat/multilingual-e5-base"):
        """
        임베딩 서비스 초기화
        
        Args:
            model_name: 사용할 임베딩 모델명 (Sentence Transformers 모델만 지원)
        """
        self.model_name = model_name
        self.model = None
        self.embedding_dimension = 768  # multilingual-e5-base 차원 수
        
        # 모델 초기화
        self._initialize_model()
    
    def _initialize_model(self):
        """임베딩 모델 초기화"""
        try:
            # Sentence Transformers 모델만 지원
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
            
            return self._generate_sentence_transformer_embeddings_batch(texts)
                
        except Exception as e:
            logger.error(f"배치 임베딩 생성 실패: {str(e)}")
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
            "provider": "sentence_transformers",
            "supports_batch": True,
            "max_batch_size": 1000
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
