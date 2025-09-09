#!/usr/bin/env python3
"""
임베딩 재생성 스크립트
기존 문서 청크들에 대해 임베딩을 재생성하고 데이터베이스에 저장합니다.
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 백엔드 모듈 경로 추가
sys.path.append('/app')

from app.services.embedding_service import EmbeddingService
from app.database.connection import get_db_url

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def regenerate_embeddings():
    """모든 문서 청크에 대해 임베딩을 재생성합니다."""
    
    # 데이터베이스 연결
    database_url = get_db_url()
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # 임베딩 서비스 초기화
    embedding_service = EmbeddingService()
    
    with SessionLocal() as db:
        try:
            # 모든 문서 청크 조회
            result = db.execute(text("""
                SELECT id, content 
                FROM document_chunks 
                WHERE content IS NOT NULL 
                AND LENGTH(content) > 0
                ORDER BY id
            """))
            
            chunks = result.fetchall()
            logger.info(f"총 {len(chunks)}개의 청크를 처리합니다.")
            
            for chunk_id, content in chunks:
                try:
                    logger.info(f"청크 {chunk_id} 처리 중...")
                    
                    # 임베딩 생성
                    embedding = embedding_service.generate_embedding(content)
                    logger.info(f"청크 {chunk_id}: 임베딩 생성 완료 (차원: {len(embedding)})")
                    
                    # 임베딩을 PostgreSQL 벡터 형식으로 변환
                    embedding_str = "[" + ",".join(map(str, embedding)) + "]"
                    
                    # 데이터베이스에 임베딩 저장
                    db.execute(text(f"""
                        UPDATE document_chunks 
                        SET embedding = '{embedding_str}'::vector 
                        WHERE id = {chunk_id}
                    """))
                    
                    db.commit()
                    logger.info(f"청크 {chunk_id}: 임베딩 저장 완료")
                    
                except Exception as e:
                    logger.error(f"청크 {chunk_id} 처리 실패: {str(e)}")
                    db.rollback()
                    continue
            
            logger.info("모든 임베딩 재생성이 완료되었습니다.")
            
        except Exception as e:
            logger.error(f"임베딩 재생성 실패: {str(e)}")
            raise

if __name__ == "__main__":
    regenerate_embeddings()
