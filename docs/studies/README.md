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

### [minio-explanation.md](./minio-explanation.md)
- **목적**: MinIO S3 호환 객체 저장소 학습 가이드
- **내용**:
  - **MinIO 기본 개념**: 고성능 분산 객체 저장소 이해
  - **S3 호환성**: Amazon S3 API와 100% 호환
  - **Company-on 역할**: 문서 파일 저장소 및 업로드/다운로드 관리
  - **Docker 설정**: 컨테이너 기반 MinIO 구성
  - **문제 해결**: 인증, 네트워크, 권한 문제 진단 및 해결
  - **성능 최적화**: 버킷 정책, 파일 구조, 보안 강화

### [redis-explanation.md](./redis-explanation.md)
- **목적**: Redis 핵심 개념과 운영 팁 정리
- **내용**: 브로커/캐시, TTL/eviction, Pub/Sub, 운영/문제 해결

### [docker-explanation.md](./docker-explanation.md)
- **목적**: Docker 실무 팁과 최적화
- **내용**: 네트워크/볼륨, 리소스 제한, 로그/헬스체크, 디버깅

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

### 파일 저장소
- **MinIO**: S3 호환 객체 저장소
- **사전 서명된 URL**: 보안적인 파일 업로드/다운로드
- **버킷 관리**: 논리적 파일 그룹화
- **파일 메타데이터**: 크기, 타입, 수정일 관리
