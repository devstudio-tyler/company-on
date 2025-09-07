"""
데이터베이스 연결 설정
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# 데이터베이스 URL 설정
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://ragbot_user:ragbot_password@localhost:5432/ragbot"
)

# SQLAlchemy 엔진 생성
engine = create_engine(
    DATABASE_URL,
    poolclass=StaticPool,
    pool_pre_ping=True,
    echo=False  # 개발 시 True로 설정하여 SQL 쿼리 로깅
)

# 세션 팩토리 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 베이스 클래스 생성
Base = declarative_base()

def get_db():
    """
    데이터베이스 세션 의존성 주입 함수
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db_url():
    """
    데이터베이스 URL 반환 함수 (Celery 태스크용)
    """
    return DATABASE_URL
