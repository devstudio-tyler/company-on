# Docker 학습 노트

## 개요
- 목적: 일관된 실행 환경, 손쉬운 배포/스케일링
- 구성: Backend, Postgres, Redis, MinIO, Celery(Worker/Beat/Flower)

## 핵심 개념
- 네트워크: 동일 compose 네트워크에서 서비스명으로 통신
- 볼륨: 데이터 지속성(Postgres, MinIO)
- 빌드/런타임 분리: 멀티스테이지 빌드 고려

## Company-on 팁
- backend: uvicorn autoreload, alembic upgrade head
- 프론트: 로컬 실행 + 백엔드 Docker(하이브리드)로 개발 속도↑
- CORS/프록시: Next rewrites 또는 절대 URL 사용

## 리소스 최적화
- 메모리/CPU 제한: compose deploy/resources
- 로그 관리: max-size, max-file 로테이션
- 헬스체크: depends_on + healthcheck로 기동 순서 보조

## 디버깅
- docker compose logs -f <svc>
- docker compose exec <svc> sh
- 네트워크 확인: docker inspect, curl로 서비스 간 통신 체크
