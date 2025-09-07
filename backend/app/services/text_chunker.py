"""
텍스트 청킹 서비스
긴 텍스트를 의미있는 청크로 분할하는 서비스
"""
import re
from typing import List, Dict, Any, Tuple
import tiktoken
import logging

logger = logging.getLogger(__name__)

class TextChunker:
    """텍스트 청킹 클래스"""
    
    def __init__(self, 
                 chunk_size: int = 512, 
                 chunk_overlap: int = 50,
                 max_chunk_size: int = 1024):
        """
        텍스트 청킹 초기화
        
        Args:
            chunk_size: 기본 청크 크기 (토큰 수)
            chunk_overlap: 청크 간 겹치는 부분 (토큰 수)
            max_chunk_size: 최대 청크 크기 (토큰 수)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.max_chunk_size = max_chunk_size
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        # 문장 분리 패턴 (한국어, 영어)
        self.sentence_pattern = re.compile(
            r'(?<=[.!?])\s+(?=[A-Z가-힣])|(?<=[。！？])\s*(?=[A-Z가-힣])'
        )
    
    def chunk_text(self, text: str, document_id: int) -> List[Dict[str, Any]]:
        """
        텍스트를 청크로 분할
        
        Args:
            text: 분할할 텍스트
            document_id: 문서 ID
            
        Returns:
            청크 리스트 (각 청크는 메타데이터 포함)
        """
        try:
            if not text.strip():
                return []
            
            # 1단계: 문장 단위로 분할
            sentences = self._split_into_sentences(text)
            
            # 2단계: 문장을 청크로 그룹화
            chunks = self._create_chunks_from_sentences(sentences, document_id)
            
            # 3단계: 청크 품질 검증 및 최적화
            optimized_chunks = self._optimize_chunks(chunks)
            
            logger.info(f"문서 {document_id}: {len(sentences)}개 문장을 {len(optimized_chunks)}개 청크로 분할")
            
            return optimized_chunks
            
        except Exception as e:
            logger.error(f"텍스트 청킹 실패: 문서 {document_id}, 에러: {str(e)}")
            raise
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """텍스트를 문장 단위로 분할"""
        # 기본 문장 분리
        sentences = self.sentence_pattern.split(text)
        
        # 빈 문장 제거 및 정리
        cleaned_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) > 10:  # 너무 짧은 문장 제외
                cleaned_sentences.append(sentence)
        
        return cleaned_sentences
    
    def _create_chunks_from_sentences(self, sentences: List[str], document_id: int) -> List[Dict[str, Any]]:
        """문장 리스트를 청크로 그룹화"""
        chunks = []
        current_chunk = []
        current_tokens = 0
        chunk_index = 0
        
        for sentence in sentences:
            sentence_tokens = len(self.tokenizer.encode(sentence))
            
            # 현재 청크에 문장을 추가할 수 있는지 확인
            if (current_tokens + sentence_tokens <= self.chunk_size or 
                len(current_chunk) == 0):  # 첫 번째 문장이거나 청크가 비어있으면 강제 추가
                
                current_chunk.append(sentence)
                current_tokens += sentence_tokens
                
                # 최대 크기 초과 시 청크 완성
                if current_tokens >= self.max_chunk_size:
                    chunk_data = self._create_chunk_data(
                        current_chunk, current_tokens, chunk_index, document_id
                    )
                    chunks.append(chunk_data)
                    
                    # 오버랩을 위한 다음 청크 시작
                    current_chunk, current_tokens = self._prepare_next_chunk(current_chunk)
                    chunk_index += 1
            else:
                # 현재 청크 완성
                chunk_data = self._create_chunk_data(
                    current_chunk, current_tokens, chunk_index, document_id
                )
                chunks.append(chunk_data)
                
                # 오버랩을 위한 다음 청크 시작
                current_chunk, current_tokens = self._prepare_next_chunk(current_chunk)
                current_chunk.append(sentence)
                current_tokens += sentence_tokens
                chunk_index += 1
        
        # 마지막 청크 처리
        if current_chunk:
            chunk_data = self._create_chunk_data(
                current_chunk, current_tokens, chunk_index, document_id
            )
            chunks.append(chunk_data)
        
        return chunks
    
    def _create_chunk_data(self, sentences: List[str], token_count: int, 
                          chunk_index: int, document_id: int) -> Dict[str, Any]:
        """청크 데이터 생성"""
        chunk_text = " ".join(sentences)
        
        return {
            "document_id": document_id,
            "chunk_index": chunk_index,
            "content": chunk_text,
            "token_count": token_count,
            "sentence_count": len(sentences),
            "char_count": len(chunk_text),
            "metadata": {
                "chunk_size": token_count,
                "sentence_count": len(sentences),
                "avg_sentence_length": token_count / len(sentences) if sentences else 0,
                "first_sentence": sentences[0][:100] if sentences else "",
                "last_sentence": sentences[-1][:100] if sentences else ""
            }
        }
    
    def _prepare_next_chunk(self, current_chunk: List[str]) -> Tuple[List[str], int]:
        """다음 청크를 위한 오버랩 준비"""
        if not current_chunk or self.chunk_overlap == 0:
            return [], 0
        
        # 오버랩 토큰 수 계산
        overlap_tokens = 0
        overlap_sentences = []
        
        # 뒤에서부터 문장을 추가하여 오버랩 크기 맞추기
        for sentence in reversed(current_chunk):
            sentence_tokens = len(self.tokenizer.encode(sentence))
            if overlap_tokens + sentence_tokens <= self.chunk_overlap:
                overlap_sentences.insert(0, sentence)
                overlap_tokens += sentence_tokens
            else:
                break
        
        return overlap_sentences, overlap_tokens
    
    def _optimize_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """청크 품질 최적화"""
        optimized_chunks = []
        
        for chunk in chunks:
            # 너무 짧은 청크는 이전 청크와 병합
            if chunk["token_count"] < self.chunk_size // 2 and optimized_chunks:
                last_chunk = optimized_chunks[-1]
                if last_chunk["token_count"] + chunk["token_count"] <= self.max_chunk_size:
                    # 청크 병합
                    merged_content = last_chunk["content"] + " " + chunk["content"]
                    merged_tokens = last_chunk["token_count"] + chunk["token_count"]
                    
                    last_chunk["content"] = merged_content
                    last_chunk["token_count"] = merged_tokens
                    last_chunk["sentence_count"] += chunk["sentence_count"]
                    last_chunk["char_count"] += chunk["char_count"]
                    last_chunk["metadata"]["chunk_size"] = merged_tokens
                    last_chunk["metadata"]["sentence_count"] = last_chunk["sentence_count"]
                    last_chunk["metadata"]["last_sentence"] = chunk["metadata"]["last_sentence"]
                    continue
            
            optimized_chunks.append(chunk)
        
        return optimized_chunks
    
    def get_chunk_statistics(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """청크 통계 정보 반환"""
        if not chunks:
            return {}
        
        token_counts = [chunk["token_count"] for chunk in chunks]
        sentence_counts = [chunk["sentence_count"] for chunk in chunks]
        
        return {
            "total_chunks": len(chunks),
            "total_tokens": sum(token_counts),
            "avg_tokens_per_chunk": sum(token_counts) / len(chunks),
            "min_tokens": min(token_counts),
            "max_tokens": max(token_counts),
            "avg_sentences_per_chunk": sum(sentence_counts) / len(sentence_counts),
            "total_sentences": sum(sentence_counts)
        }
