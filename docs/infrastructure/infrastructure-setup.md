# 인프라 설정 세부 가이드

## 🎯 인프라 설정 목표
- 로컬 개발 환경 구축 ✅
- 모든 서비스가 Docker로 정상 기동 ✅
- 데이터베이스 스키마 생성 완료 ✅
- 개발 도구 및 환경 설정 완료 ✅
- **Celery 백그라운드 워커 설정 완료** ✅
- **문서 처리 파이프라인 자동화** ✅
- **하이브리드 검색 시스템 구현** ✅
- **SSE 실시간 알림 시스템 구현** ✅


---

## 🐳 1. Docker Compose 설정 (2시간)

### 1.1 프로젝트 구조 생성 (30분)
```bash
# 프로젝트 루트 디렉토리 구조
ragbot/
├── docker-compose.yml
├── docker-compose.dev.yml
├── .env.example
├── .env
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   └── src/
├── scripts/
│   ├── init-db.sh
│   └── setup.sh
└── data/
    ├── postgres/
    ├── redis/
    └── minio/
```

**작업 내용:**
- [ ] 프로젝트 폴더 구조 생성
- [ ] 각 서비스별 Dockerfile 생성
- [ ] 환경 변수 파일 템플릿 생성

### 1.2 Docker Compose 파일 작성 (1시간)
```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: ragbot
      POSTGRES_USER: ragbot_user
      POSTGRES_PASSWORD: ragbot_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-db.sh:/docker-entrypoint-initdb.d/init-db.sh
    networks:
      - ragbot-network

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - ragbot-network

  minio:
    image: minio/minio:latest
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin123
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data
    command: server /data --console-address ":9001"
    networks:
      - ragbot-network

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://ragbot_user:ragbot_password@postgres:5432/ragbot
      - REDIS_URL=redis://redis:6379
      - MINIO_ENDPOINT=minio:9000
      - MINIO_ACCESS_KEY=minioadmin
      - MINIO_SECRET_KEY=minioadmin123
    depends_on:
      - postgres
      - redis
      - minio
    volumes:
      - ./backend:/app
    networks:
      - ragbot-network

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    depends_on:
      - backend
    volumes:
      - ./frontend:/app
      - /app/node_modules
    networks:
      - ragbot-network

volumes:
  postgres_data:
  redis_data:
  minio_data:

networks:
  ragbot-network:
    driver: bridge
```

**작업 내용:**
- [ ] PostgreSQL + pgvector 컨테이너 설정
- [ ] Redis 컨테이너 설정
- [ ] MinIO 컨테이너 설정
- [ ] 백엔드 서비스 컨테이너 설정
- [ ] 프론트엔드 서비스 컨테이너 설정
- [ ] 네트워크 및 볼륨 설정

### 1.3 환경 변수 설정 (30분)
```bash
# .env.example
# Database
DATABASE_URL=postgresql://ragbot_user:ragbot_password@localhost:5432/ragbot
POSTGRES_DB=ragbot
POSTGRES_USER=ragbot_user
POSTGRES_PASSWORD=ragbot_password

# Redis
REDIS_URL=redis://localhost:6379

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123

# API Keys
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# JWT
JWT_SECRET_KEY=your_jwt_secret_key_here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application
DEBUG=True
LOG_LEVEL=INFO
```

**작업 내용:**
- [ ] .env.example 파일 생성
- [ ] .env 파일 생성 (실제 값 입력)
- [ ] 환경 변수 검증

---

## 🗄️ 2. 데이터베이스 스키마 설정 (2시간)

### 2.1 Alembic 마이그레이션 설정 (1시간)
```python
# backend/alembic.ini
[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url = postgresql://ragbot_user:ragbot_password@localhost:5432/ragbot

[post_write_hooks]
hooks = black
black.type = console_scripts
black.entrypoint = black
black.options = -l 79 REVISION_SCRIPT_FILENAME
```

**작업 내용:**
- [ ] Alembic 초기화 (`alembic init alembic`)
- [ ] alembic.ini 설정 파일 수정
- [ ] env.py 파일 설정 (SQLAlchemy 모델 연결)
- [ ] 첫 번째 마이그레이션 생성

### 2.2 데이터베이스 스키마 생성 (1시간)
```python
# backend/app/models/__init__.py
from .chat import ChatSession, ChatMessage, ChatSessionEmbedding, ChatMessageEmbedding
from .document import Document, DocumentChunk, DocumentEmbedding
from .user import User, Company, UserPreferences

__all__ = [
    "ChatSession", "ChatMessage", "ChatSessionEmbedding", "ChatMessageEmbedding",
    "Document", "DocumentChunk", "DocumentEmbedding",
    "User", "Company", "UserPreferences"
]
```

**작업 내용:**
- [ ] SQLAlchemy 모델 정의
  - [ ] ChatSession 모델
  - [ ] ChatMessage 모델
  - [ ] Document 모델
  - [ ] DocumentChunk 모델
  - [ ] User, Company 모델
- [ ] 마이그레이션 파일 생성 (`alembic revision --autogenerate -m "Initial schema"`)
- [ ] 마이그레이션 실행 (`alembic upgrade head`)

---

## 🛠️ 3. 개발 도구 설정 (2시간)

### 3.1 Python 백엔드 환경 설정 (1시간)
```bash
# backend/requirements.txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
alembic==1.12.1
psycopg2-binary==2.9.9
pgvector==0.2.4
redis==5.0.1
celery==5.3.4
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
minio==7.2.0
openai==1.3.7
anthropic==0.7.8
sentence-transformers==2.2.2
pydantic==2.5.0
pydantic-settings==2.1.0
python-dotenv==1.0.0
```

**작업 내용:**
- [ ] Python 가상환경 생성 (`python -m venv venv`)
- [ ] 가상환경 활성화 (`source venv/bin/activate`)
- [ ] requirements.txt 생성 및 의존성 설치
- [ ] VS Code 설정 (.vscode/settings.json)

### 3.2 Node.js 프론트엔드 환경 설정 (1시간)
```json
// frontend/package.json
{
  "name": "ragbot-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  },
  "dependencies": {
    "next": "14.0.3",
    "react": "^18",
    "react-dom": "^18",
    "@tanstack/react-query": "^5.8.4",
    "axios": "^1.6.2",
    "react-dropzone": "^14.2.3",
    "react-virtual": "^2.10.4",
    "pdfjs-dist": "^3.11.174",
    "docx-preview": "^0.1.4",
    "lucide-react": "^0.294.0",
    "tailwindcss": "^3.3.6",
    "autoprefixer": "^10.4.16",
    "postcss": "^8.4.32"
  },
  "devDependencies": {
    "typescript": "^5",
    "@types/node": "^20",
    "@types/react": "^18",
    "@types/react-dom": "^18",
    "eslint": "^8",
    "eslint-config-next": "14.0.3"
  }
}
```

**작업 내용:**
- [ ] Node.js 프로젝트 초기화 (`npm init -y`)
- [ ] Next.js 설치 (`npx create-next-app@latest .`)
- [ ] 필요한 패키지 설치
- [ ] TypeScript 설정 (tsconfig.json)
- [ ] Tailwind CSS 설정

---

## 🔧 4. 초기화 스크립트 작성 (1시간)

### 4.1 데이터베이스 초기화 스크립트 (30분)
```bash
#!/bin/bash
# scripts/init-db.sh

# pgvector 확장 설치
psql -U ragbot_user -d ragbot -c "CREATE EXTENSION IF NOT EXISTS vector;"

# 초기 데이터 삽입
psql -U ragbot_user -d ragbot -c "
INSERT INTO companies (id, name, created_at) VALUES 
(1, 'Vibers AI', NOW()),
(2, 'Test Company', NOW())
ON CONFLICT (id) DO NOTHING;

INSERT INTO users (id, company_id, email, name, created_at) VALUES 
(1, 1, 'admin@vibers.ai', 'Admin User', NOW()),
(2, 1, 'test@vibers.ai', 'Test User', NOW())
ON CONFLICT (id) DO NOTHING;
"
```

**작업 내용:**
- [ ] 데이터베이스 초기화 스크립트 작성
- [ ] pgvector 확장 설치
- [ ] 샘플 데이터 삽입

### 4.2 전체 설정 스크립트 (30분)
```bash
#!/bin/bash
# scripts/setup.sh

echo "🚀 RAGbot 인프라 설정 시작..."

# Docker 컨테이너 빌드 및 시작
echo "📦 Docker 컨테이너 빌드 중..."
docker-compose build

echo "🔄 서비스 시작 중..."
docker-compose up -d

# 서비스 상태 확인
echo "⏳ 서비스 시작 대기 중..."
sleep 30

# 헬스체크
echo "🏥 서비스 상태 확인 중..."
curl -f http://localhost:8000/health || echo "❌ 백엔드 서비스 실패"
curl -f http://localhost:3000 || echo "❌ 프론트엔드 서비스 실패"

echo "✅ 인프라 설정 완료!"
echo "📊 서비스 접속 정보:"
echo "  - 프론트엔드: http://localhost:3000"
echo "  - 백엔드 API: http://localhost:8000"
echo "  - MinIO 콘솔: http://localhost:9001"
echo "  - 데이터베이스: localhost:5432"
```

**작업 내용:**
- [ ] 전체 설정 자동화 스크립트 작성
- [ ] 서비스 상태 확인 로직
- [ ] 헬스체크 엔드포인트 구현

---

## ✅ 5. 검증 및 테스트 (1시간)

### 5.1 서비스 상태 확인 (30분)
**작업 내용:**
- [ ] PostgreSQL 연결 테스트
- [ ] Redis 연결 테스트
- [ ] MinIO 연결 테스트
- [ ] 백엔드 API 헬스체크
- [ ] 프론트엔드 접속 확인

### 5.2 데이터베이스 스키마 검증 (30분)
**작업 내용:**
- [ ] 모든 테이블 생성 확인
- [ ] 인덱스 생성 확인
- [ ] 외래키 제약조건 확인
- [ ] 샘플 데이터 삽입 테스트

---

## 🎯 완료 기준

### ✅ M1 완료 기준
- [ ] `docker-compose up -d` 명령으로 모든 서비스 정상 기동
- [ ] http://localhost:8000/health 응답 확인
- [ ] http://localhost:3000 접속 확인
- [ ] 데이터베이스에 모든 테이블 생성 완료
- [ ] 샘플 데이터 삽입 성공

### 🔍 검증 방법
```bash
# 서비스 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs backend
docker-compose logs celery-worker
docker-compose logs celery-beat

# 데이터베이스 연결 테스트
docker-compose exec postgres psql -U ragbot_user -d ragbot -c "\dt"

# API 테스트
curl http://localhost:8000/health

# Celery 워커 상태 확인
curl http://localhost:5555/api/workers

# 문서 처리 파이프라인 테스트
curl -X POST "http://localhost:8000/api/v1/documents/processing/stats"
```

---

## 🚨 문제 해결 가이드

### 일반적인 문제들
1. **포트 충돌**: 5432, 6379, 8000, 3000, 9000, 9001 포트 사용 중
2. **권한 문제**: Docker 볼륨 마운트 권한 오류
3. **메모리 부족**: Docker 메모리 할당 부족
4. **네트워크 문제**: 컨테이너 간 통신 실패

### 해결 방법
```bash
# 포트 사용 중인 프로세스 확인
lsof -i :5432
lsof -i :6379
lsof -i :8000
lsof -i :3000

# Docker 리소스 확인
docker system df
docker system prune

# 컨테이너 재시작
docker-compose restart
```

이제 이 가이드를 따라 인프라 설정을 단계별로 진행할 수 있습니다!
