# 인프라 문서

Company-on 프로젝트의 인프라 설정 및 운영 관련 문서입니다.

## 📋 문서 목록

### [infrastructure-setup.md](./infrastructure-setup.md)
- **목적**: Docker 기반 개발 환경 구축 가이드
- **내용**:
  - Docker Compose 서비스 구성
  - PostgreSQL + pgvector 설정
  - Redis 캐시 설정
  - MinIO 객체 저장소 설정
  - 네트워크 및 볼륨 구성
  - 환경 변수 설정

## 🏗️ 인프라 구성

### 핵심 서비스
- **PostgreSQL 16 + pgvector**: 메인 데이터베이스
- **Redis 7**: 캐시 및 세션 저장소
- **MinIO**: 객체 저장소 (파일 업로드/다운로드)
- **FastAPI**: 백엔드 API 서버
- **Next.js**: 프론트엔드 웹 애플리케이션

### 네트워크 구성
- **company-on-network**: 모든 서비스 간 통신
- **포트 매핑**:
  - 8000: FastAPI (백엔드)
  - 3000: Next.js (프론트엔드)
  - 5432: PostgreSQL
  - 6379: Redis
  - 9000-9001: MinIO

## 🚀 빠른 시작

```bash
# 전체 서비스 시작
docker-compose up -d

# 서비스 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs -f backend

# 서비스 중지
docker-compose down
```

## 🔧 개발 도구

- **Alembic**: 데이터베이스 마이그레이션
- **pgAdmin**: PostgreSQL 관리 (선택사항)
- **Redis Commander**: Redis 관리 (선택사항)
- **MinIO Console**: 객체 저장소 관리
