# RAG 기반 문서 검색 및 챗봇 시스템

## 📚 프로젝트 개요

이 프로젝트는 다양한 문서 형식(PDF, DOCX, XLSX, CSV, JPG, PNG)을 업로드하고, AI 기반 임베딩을 통해 벡터 데이터베이스에 저장한 후, 사용자의 질문에 대해 관련 문서를 검색하여 정확한 답변을 제공하는 RAG(Retrieval-Augmented Generation) 시스템입니다.

### 주요 기능
- 🔄 **다양한 문서 형식 지원**: PDF, DOCX, XLSX, CSV, JPG, PNG
- 🤖 **OCR 텍스트 추출**: 이미지 파일의 텍스트 인식
- 📊 **구조화된 데이터 처리**: Excel/CSV 파일의 테이블 형태 처리
- 🔍 **의미적 검색**: 벡터 임베딩을 활용한 정확한 문서 검색
- 💬 **실시간 챗봇**: AI 모델 기반 자연어 질의응답
- 📱 **반응형 웹 인터페이스**: 모던하고 직관적인 사용자 경험

## 🛠 기술 스택 및 선택 이유

### Frontend
- **Next.js 15.5.2** + **TypeScript**
  - **선택 이유**: 
    - Server-Side Rendering을 통한 SEO 최적화 및 빠른 초기 로딩
    - TypeScript로 타입 안정성 확보
    - React 18의 최신 기능 활용 (Concurrent Features, Suspense)
    - API Routes를 통한 백엔드 프록시 설정

- **Tailwind CSS**
  - **선택 이유**: 
    - 유틸리티 퍼스트 CSS 프레임워크로 빠른 스타일링
    - 반응형 디자인 쉬운 구현
    - 번들 크기 최적화 (사용하지 않는 CSS 자동 제거)

- **Lucide React**
  - **선택 이유**: 
    - 경량화된 아이콘 라이브러리
    - 일관된 디자인 시스템 구축

### Backend
- **FastAPI** + **Python 3.11**
  - **선택 이유**: 
    - 고성능 비동기 웹 프레임워크
    - 자동 OpenAPI 문서 생성
    - Pydantic을 통한 데이터 검증
    - WebSocket 지원으로 실시간 기능 구현

- **PostgreSQL 16** + **pgvector**
  - **선택 이유**: 
    - 벡터 데이터베이스 기능 내장 (pgvector extension)
    - ACID 트랜잭션 지원으로 데이터 일관성 보장
    - 복잡한 쿼리와 인덱싱 최적화
    - 대용량 데이터 처리 성능

- **Redis**
  - **선택 이유**: 
    - Celery 메시지 브로커로 사용
    - 세션 및 캐시 스토리지
    - 고성능 인메모리 데이터베이스

- **MinIO**
  - **선택 이유**: 
    - S3 호환 오브젝트 스토리지
    - 대용량 파일 저장 및 관리
    - 온프레미스 환경에서 안전한 파일 저장

### AI/ML 모델
- **SentenceTransformers** (paraphrase-multilingual-MiniLM-L12-v2)
  - **선택 이유**: 
    - 다국어 지원 (한국어 포함)
    - 384차원 벡터로 효율적인 메모리 사용
    - 문서 검색에 최적화된 성능

- **Google Gemma 3 12B** (via OpenRouter)
  - **선택 이유**: 
    - 최신 대규모 언어 모델
    - 한국어 성능 우수
    - API 기반으로 인프라 부담 최소화
    - 추후 Vertex AI로 확장 가능

- **Tesseract OCR**
  - **선택 이유**: 
    - 오픈소스 OCR 엔진
    - 다양한 언어 지원 (한국어 + 영어)
    - 이미지 품질에 따른 인식률 최적화

### 비동기 작업 처리
- **Celery** + **Flower**
  - **선택 이유**: 
    - 문서 처리 작업의 비동기 처리
    - 작업 큐 모니터링 및 관리
    - 확장 가능한 워커 아키텍처

## 🚀 실행 방법

#### 사전 요구사항
- Docker & Docker Compose
- Node.js 18+ (로컬 프론트엔드 실행 시)
- Python 3.11+ (로컬 백엔드 실행 시)

### 방법 1: Docker 실행 (개발용 - 느림)
```bash
# 모든 서비스 시작
docker-compose up -d

# 데이터베이스 마이그레이션
docker-compose exec backend alembic upgrade head

# 프론트엔드 실행
cd frontend
npm install
npm run dev
```

### 방법 2: 로컬 실행 (권장 - 빠름)
Docker 컨테이너에서 실행하면 macOS에서 성능이 크게 저하될 수 있습니다. 로컬 실행을 권장합니다.

#### 2-1. 데이터베이스 및 Redis 실행 (Docker)
```bash
# 데이터베이스와 Redis만 Docker로 실행
docker-compose up -d postgres redis minio

# 데이터베이스 마이그레이션
docker-compose exec postgres psql -U postgres -d ragbot -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

#### 2-2. 백엔드 로컬 실행
```bash
# 백엔드 디렉토리로 이동
cd backend

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # macOS/Linux
# 또는
venv\Scripts\activate  # Windows

# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정
cp .env.example .env
# .env 파일에서 OpenRouter API 키 등 설정

# 백엔드 서버 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 2-3. Celery Worker 로컬 실행
```bash
# 백엔드 디렉토리에서 (가상환경 활성화 상태)
celery -A app.celery worker --loglevel=info

# 별도 터미널에서 Celery Beat 실행 (선택사항)
celery -A app.celery beat --loglevel=info

# Flower 모니터링 (선택사항)
celery -A app.celery flower --port=5555
```

#### 2-4. 프론트엔드 로컬 실행
```bash
# 프론트엔드 디렉토리로 이동
cd frontend

# 의존성 설치
npm install

# 프론트엔드 서버 실행
npm run dev
```

### 3. 서비스 접속
- **웹 애플리케이션**: http://localhost:3000
- **백엔드 API**: http://localhost:8000/docs
- **Celery Flower**: http://localhost:5555
- **MinIO Console**: http://localhost:9001

### 성능 비교
- **Docker 실행**: 개발 환경에서 느림, 파일 시스템 공유 오버헤드
- **로컬 실행**: 빠른 응답속도, 실시간 코드 변경 반영, 디버깅 용이

## 🏗 시스템 아키텍처

### 전체 아키텍처 다이어그램

```mermaid
graph TB
    subgraph "Frontend Layer"
        UI[Next.js Frontend<br/>Port: 3000]
    end
    
    subgraph "API Gateway"
        API[FastAPI Backend<br/>Port: 8000]
    end
    
    subgraph "Database Layer"
        PG[(PostgreSQL + pgvector<br/>Port: 5432)]
        RD[(Redis<br/>Port: 6379)]
    end
    
    subgraph "Storage Layer"
        MINIO[MinIO Object Storage<br/>Port: 9000/9001]
    end
    
    subgraph "Processing Layer"
        CW[Celery Worker]
        CB[Celery Beat]
        CF[Celery Flower<br/>Port: 5555]
    end
    
    subgraph "AI/ML Services"
        EMB[SentenceTransformers<br/>Embedding Service]
        OCR[Tesseract OCR<br/>Image Processing]
        LLM[Gemma 3 12B<br/>via OpenRouter]
    end
    
    UI --> API
    API --> PG
    API --> RD
    API --> MINIO
    API --> CW
    CW --> EMB
    CW --> OCR
    API --> LLM
    CF --> RD
    CB --> RD
```

### 데이터 플로우

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant A as API
    participant M as MinIO
    participant W as Celery Worker
    participant E as Embedding Service
    participant D as PostgreSQL
    participant L as LLM Service
    
    U->>F: 파일 업로드
    F->>A: POST /upload
    A->>M: 원본 파일 저장
    A->>D: 문서 메타데이터 저장 (status: processing)
    A->>W: 문서 처리 작업 큐에 추가
    A->>F: 업로드 완료 응답
    
    W->>M: 파일 다운로드
    W->>W: 텍스트 추출 (PDF/DOCX/Excel/OCR)
    W->>W: 텍스트 청킹
    W->>E: 임베딩 생성
    W->>D: 청크 및 임베딩 저장
    W->>D: 문서 상태 업데이트 (status: completed)
    
    U->>F: 질문 입력
    F->>A: POST /chat
    A->>E: 질문 임베딩 생성
    A->>D: 유사 문서 검색
    A->>L: LLM 답변 생성
    A->>F: 답변 반환
```

### 문서 처리 파이프라인

```mermaid
graph LR
    subgraph "File Upload"
        UP[파일 업로드] --> VAL[파일 검증]
        VAL --> STORE[MinIO 저장]
    end
    
    subgraph "Text Extraction"
        STORE --> PDF[PDF 텍스트 추출]
        STORE --> DOCX[DOCX 텍스트 추출]
        STORE --> EXCEL[Excel/CSV 처리]
        STORE --> IMG[이미지 OCR]
    end
    
    subgraph "Processing"
        PDF --> CHUNK[텍스트 청킹]
        DOCX --> CHUNK
        EXCEL --> CHUNK
        IMG --> CHUNK
        CHUNK --> EMB[임베딩 생성]
    end
    
    subgraph "Storage"
        EMB --> VDB[(벡터 DB 저장)]
        EMB --> META[(메타데이터 저장)]
    end
```

### 주요 컴포넌트 설명

#### 1. **문서 업로드 및 저장**
- 사용자가 업로드한 파일을 MinIO에 안전하게 저장
- PostgreSQL에 문서 메타데이터 기록 (상태: processing)

#### 2. **비동기 문서 처리**
- Celery Worker가 백그라운드에서 문서 처리 작업 수행
- 파일 타입에 따른 적절한 텍스트 추출 방법 선택

#### 3. **텍스트 추출 및 청킹**
- **PDF/DOCX**: PyMuPDF, python-docx 라이브러리 사용
- **Excel/CSV**: pandas 라이브러리로 구조화된 데이터 처리
- **이미지**: Tesseract OCR로 텍스트 인식
- 추출된 텍스트를 적절한 크기로 청킹

#### 4. **임베딩 및 벡터 저장**
- SentenceTransformers로 각 청크의 벡터 임베딩 생성
- pgvector를 통해 PostgreSQL에 벡터 저장
- HNSW 인덱스를 통한 고속 유사도 검색

#### 5. **질의응답 시스템**
- 사용자 질문을 벡터로 변환
- pgvector의 코사인 유사도를 통한 관련 문서 검색
- 검색된 컨텍스트와 함께 LLM에 답변 요청

## 📋 API 엔드포인트

### 문서 관리
- `GET /api/v1/documents` - 문서 목록 조회
- `POST /api/v1/documents/upload` - 문서 업로드
- `GET /api/v1/documents/{id}/download` - 문서 다운로드
- `GET /api/v1/documents/{id}/chunks` - 문서 청크 조회

### 검색 및 챗봇
- `POST /api/v1/search` - 문서 검색
- `POST /api/v1/chat` - 챗봇 대화
- `GET /api/v1/chat/sessions` - 채팅 세션 관리

### 상태 확인
- `GET /health` - 서비스 헬스체크
- `GET /api/v1/upload-status/{session_id}` - 업로드 상태 확인

## 🚀 실행 방법

### 사전 요구사항
- Docker & Docker Compose
- Node.js 18+ (프론트엔드 개발용)
- Python 3.11+ (백엔드 개발용)

### ⚡ 빠른 시작 (하이브리드 환경)

가장 빠르게 개발을 시작하려면:

```bash
# 1. 백엔드 서비스 시작 (Docker)
docker-compose up -d postgres redis minio backend celery-worker celery-beat celery-flower

# 2. 프론트엔드 시작 (로컬)
cd frontend
npm install
npm run dev

# 3. 브라우저에서 접속
open http://localhost:3000
```

**완료!** 🎉 이제 개발을 시작할 수 있습니다.

### 1. 전체 시스템 실행 (Docker Compose)

#### 백엔드 서비스 시작
```bash
# 프로젝트 루트 디렉토리에서
docker-compose up -d

# 또는 특정 서비스만 시작
docker-compose up -d postgres redis minio backend celery-worker celery-beat celery-flower
```

#### 프론트엔드 개발 서버 시작
```bash
# 프론트엔드 디렉토리에서
cd frontend
npm install
npm run dev
```

### 2. 하이브리드 개발 환경 (권장) 🚀

이 방법은 백엔드 인프라와 API 서버는 Docker로 실행하고, 프론트엔드는 로컬에서 개발하는 방식입니다. 개발 효율성이 높고 디버깅이 용이합니다.

#### 2-1. 백엔드 인프라 서비스 시작 (Docker)
```bash
# 1. 인프라 서비스들만 Docker로 실행
docker-compose up -d postgres redis minio

# 2. 백엔드 API 서버와 작업 처리 서비스들 Docker로 실행
docker-compose up -d backend celery-worker celery-beat celery-flower

# 3. 서비스 상태 확인
docker-compose ps
```

#### 2-2. 프론트엔드 로컬 개발 환경 설정
```bash
# 1. 프론트엔드 디렉토리로 이동
cd frontend

# 2. 의존성 설치 (최초 1회)
npm install

# 3. 개발 서버 시작
npm run dev
```

#### 2-3. 서비스 접속 정보
- **프론트엔드**: http://localhost:3000 (또는 3001)
- **백엔드 API**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs
- **MinIO 콘솔**: http://localhost:9001 (minioadmin/minioadmin)
- **Celery Flower**: http://localhost:5555

#### 2-4. 하이브리드 환경의 장단점

##### 장점 ✅
- **빠른 개발**: 프론트엔드 Hot Reload 즉시 반영
- **디버깅 용이**: 브라우저 개발자 도구와 VS Code 디버거 사용 가능
- **리소스 효율**: 백엔드 인프라만 Docker로 격리
- **환경 일관성**: 프로덕션과 동일한 백엔드 환경
- **유연성**: 프론트엔드와 백엔드를 독립적으로 개발 가능

##### 단점 ⚠️
- **환경 설정**: 로컬에 Node.js 설치 필요
- **포트 관리**: 프론트엔드 포트 충돌 가능성
- **CORS 설정**: 프론트엔드-백엔드 간 CORS 설정 필요

##### 언제 사용하나요?
- 🎯 **프론트엔드 중심 개발** 시
- 🎯 **UI/UX 반복 개발** 시
- 🎯 **브라우저 디버깅**이 중요한 경우
- 🎯 **개발 속도**를 우선시하는 경우

### 3. 환경 변수 설정

#### 백엔드 환경 변수
```bash
# backend/.env 파일 생성
cd backend
cp .env.example .env  # 예시 파일이 있다면

# 또는 직접 생성
cat > .env << EOF
DEBUG=False
OPENROUTER_API_KEY=your_openrouter_api_key_here
GEMMA_MODEL=google/gemma-3-12b-it:free
POSTGRES_URL=postgresql://ragbot_user:ragbot_password@localhost:5432/ragbot
REDIS_URL=redis://localhost:6379
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET_NAME=documents
EOF
```

#### 프론트엔드 환경 변수
```bash
# frontend/.env.local 파일 생성 (필요시)
cd frontend
cat > .env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
EOF
```

### 4. 데이터베이스 초기화

#### 마이그레이션 실행
```bash
# Docker 컨테이너 내에서 실행
docker-compose exec backend alembic upgrade head

# 또는 로컬에서 실행 (가상환경 활성화 후)
cd backend
source venv/bin/activate  # Linux/Mac
# 또는
# venv\Scripts\activate  # Windows
alembic upgrade head
```

### 5. 서비스 확인

#### 백엔드 서비스 상태 확인
```bash
# 헬스체크
curl http://localhost:8000/health

# API 문서 확인
open http://localhost:8000/docs
```

#### 프론트엔드 서비스 확인
```bash
# 프론트엔드 접속
open http://localhost:3000
# 또는 포트가 사용 중인 경우
open http://localhost:3001
```

#### 관리 도구 접속
- **MinIO 콘솔**: http://localhost:9001 (minioadmin/minioadmin)
- **Celery Flower**: http://localhost:5555
- **PostgreSQL**: localhost:5432 (ragbot_user/ragbot_password)
- **Redis**: localhost:6379

### 6. 하이브리드 환경 전용 가이드

#### 6-1. 백엔드 로컬 개발 (선택사항)
하이브리드 환경에서 백엔드도 로컬에서 개발하고 싶다면:

```bash
# 1. 인프라 서비스만 Docker로 실행
docker-compose up -d postgres redis minio

# 2. 백엔드 로컬 개발 환경 설정
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는 venv\Scripts\activate  # Windows

# 3. 의존성 설치
pip install -r requirements.txt

# 4. 환경 변수 설정
cat > .env << EOF
DEBUG=False
OPENROUTER_API_KEY=your_openrouter_api_key_here
GEMMA_MODEL=google/gemma-3-12b-it:free
POSTGRES_URL=postgresql://ragbot_user:ragbot_password@localhost:5432/ragbot
REDIS_URL=redis://localhost:6379
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET_NAME=documents
EOF

# 5. 데이터베이스 마이그레이션
alembic upgrade head

# 6. 백엔드 서버 시작
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 6-2. Celery Worker 로컬 실행 (선택사항)
```bash
cd backend
source venv/bin/activate
celery -A app.celery_app worker --loglevel=info
```

#### 6-3. Celery Beat 로컬 실행 (선택사항)
```bash
cd backend
source venv/bin/activate
celery -A app.celery_app beat --loglevel=info
```

#### 6-4. 하이브리드 환경 문제 해결

##### 포트 충돌 해결
```bash
# 사용 중인 포트 확인
lsof -i :3000  # 프론트엔드
lsof -i :8000  # 백엔드
lsof -i :5432  # PostgreSQL

# 프로세스 종료
kill -9 <PID>
```

##### Docker 컨테이너 관리
```bash
# 특정 서비스만 재시작
docker-compose restart backend

# 로그 확인
docker-compose logs backend
docker-compose logs postgres

# 컨테이너 상태 확인
docker-compose ps
```

##### 프론트엔드 프록시 문제 해결
```bash
# Next.js 프록시 설정 확인
cat frontend/next.config.js

# 프론트엔드 재시작
cd frontend
npm run dev
```

##### CORS 문제 해결
```bash
# 백엔드 CORS 설정 확인
grep -A 5 "allow_origins" backend/app/main.py

# 백엔드 재시작
docker-compose restart backend
```

### 7. 개발 모드 실행 (전체 로컬)

### 7. 프로덕션 배포

#### 프론트엔드 빌드
```bash
cd frontend
npm run build
npm run start
```

#### 백엔드 프로덕션 실행
```bash
# Docker Compose로 전체 스택 실행
docker-compose -f docker-compose.prod.yml up -d
```

### 8. 문제 해결

#### 포트 충돌 해결
```bash
# 사용 중인 포트 확인
lsof -i :3000
lsof -i :8000
lsof -i :5432

# 프로세스 종료
kill -9 <PID>
```

#### Docker 컨테이너 재시작
```bash
# 특정 서비스 재시작
docker-compose restart backend

# 전체 재시작
docker-compose down
docker-compose up -d
```

#### 로그 확인
```bash
# 전체 로그
docker-compose logs

# 특정 서비스 로그
docker-compose logs backend
docker-compose logs frontend
```

#### 데이터 초기화
```bash
# 볼륨 삭제 (주의: 모든 데이터 삭제됨)
docker-compose down -v
docker-compose up -d
```

### 9. 개발 워크플로우

#### 9-1. 하이브리드 환경 개발 워크플로우 (권장)
```bash
# 1. 백엔드 인프라 및 API 서버 시작
docker-compose up -d postgres redis minio backend celery-worker celery-beat celery-flower

# 2. 프론트엔드 개발 서버 시작
cd frontend && npm run dev

# 3. 개발 및 테스트
# - 프론트엔드: Hot Reload로 즉시 반영
# - 백엔드: Docker 로그로 실시간 확인
# - API 테스트: http://localhost:8000/docs

# 4. 코드 커밋
```

#### 9-2. 전체 Docker 환경 개발 워크플로우
```bash
# 1. 전체 서비스 시작
docker-compose up -d

# 2. 프론트엔드 개발 서버 시작 (선택사항)
cd frontend && npm run dev

# 3. 개발 및 테스트
# 4. 코드 커밋
```

#### 2. 데이터베이스 스키마 변경
```bash
# 1. 모델 수정
# 2. 마이그레이션 생성
docker-compose exec backend alembic revision --autogenerate -m "description"

# 3. 마이그레이션 적용
docker-compose exec backend alembic upgrade head
```

#### 3. 의존성 업데이트
```bash
# 백엔드
cd backend
pip install -r requirements.txt

# 프론트엔드
cd frontend
npm install
```

## 📝 추가 정보

### 현재 구현된 기능
- ✅ **문서 업로드**: PDF, DOCX, XLSX, CSV, PNG, JPG 지원
- ✅ **OCR 처리**: 이미지 파일의 텍스트 추출
- ✅ **벡터 검색**: 의미적 유사도 기반 문서 검색
- ✅ **실시간 채팅**: 스트리밍 응답 지원
- ✅ **세션 관리**: 채팅 세션 생성, 수정, 삭제, 고정
- ✅ **실패 처리**: 업로드/처리 실패 시 재시도 기능
- ✅ **검색 필터링**: 유사도 임계값 기반 결과 필터링

### 주요 개선사항
- **스트리밍 성능 최적화**: 디바운싱과 useRef를 통한 실시간 응답 개선
- **검색 품질 향상**: 60% 유사도 임계값으로 관련성 높은 결과만 반환
- **이미지 파일 지원**: 유사도 점수 표시 및 원본 이미지 미리보기
- **세션 관리 시스템**: 완전한 CRUD 기능과 실시간 UI 업데이트
- **에러 처리**: 포괄적인 에러 핸들링과 사용자 피드백

### 개발 환경 설정 팁
1. **포트 충돌 해결**: 3000번 포트가 사용 중이면 자동으로 3001번으로 변경
2. **환경 변수**: OpenRouter API 키를 반드시 설정해야 정상 작동
3. **데이터베이스**: PostgreSQL + pgvector 확장 필요
4. **의존성**: Python 3.11+ 및 Node.js 18+ 권장

### 성능 최적화
- **벡터 인덱싱**: HNSW 인덱스를 통한 고속 유사도 검색
- **청킹 전략**: 의미적 단위로 텍스트 분할
- **캐싱**: Redis를 통한 세션 및 임시 데이터 캐싱
- **비동기 처리**: Celery를 통한 백그라운드 문서 처리

