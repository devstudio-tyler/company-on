# 학습 자료

Company-on 프로젝트 개발 과정에서 학습한 기술 개념 및 자료입니다.

## 📋 문서 목록

### [database-concepts-explanation.md](./database-concepts-explanation.md)
- **목적**: 데이터베이스 설계 시 고려해야 할 핵심 개념 설명
- **내용**:
  - **임베딩 (Embedding)**: 벡터화 전략 및 저장 방식
  - **인덱스 (Index)**: HNSW vs IVFFlat 성능 비교
  - **파티셔닝 (Partitioning)**: 대용량 데이터 분할 전략
  - 실제 프로젝트 적용 방안 및 선택 기준

### [celery-explanation.md](./celery-explanation.md)
- **목적**: Celery 백그라운드 작업 큐 학습 가이드
- **내용**:
  - **Celery 기본 개념**: 분산 비동기 작업 큐 이해
  - **아키텍처**: Producer, Broker, Worker, Result Backend
  - **고급 기능**: 큐 라우팅, 재시도, 주기적 작업
  - **Docker 환경**: 컨테이너 기반 Celery 설정
  - **모니터링**: Flower를 통한 실시간 모니터링
  - **Company-on 적용 사례**: 문서 처리 파이프라인 자동화

## 🎯 학습 목표

### 데이터베이스 최적화
- 벡터 검색 성능 향상
- 대용량 데이터 처리 효율성
- 확장성 고려한 설계

### 기술 선택 기준
- **임베딩**: 세션별 저장 (선택됨)
- **인덱스**: HNSW 사용 (선택됨)
- **파티셔닝**: 현재 미적용, 향후 확장 고려

## 📚 관련 기술

### 데이터베이스
- **PostgreSQL**: 메인 데이터베이스
- **pgvector**: 벡터 검색 확장
- **HNSW**: 계층적 네비게이션 소규모 세계 인덱스
- **JSONB**: 유연한 메타데이터 저장

### 백그라운드 처리
- **Celery**: 분산 비동기 작업 큐
- **Redis**: 메시지 브로커 및 결과 백엔드
- **Flower**: Celery 모니터링 도구
- **Docker**: 컨테이너 기반 워커 관리
