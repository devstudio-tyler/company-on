# Celery 백그라운드 작업 큐 학습 가이드

## 📋 Celery란?

**Celery**는 Python으로 작성된 **분산 비동기 작업 큐(Distributed Task Queue)**입니다. 시간이 오래 걸리는 작업을 백그라운드에서 처리하여 웹 애플리케이션의 응답성을 향상시키는 도구입니다.

### 🎯 주요 특징

- **비동기 처리**: 시간이 오래 걸리는 작업을 백그라운드에서 처리
- **분산 처리**: 여러 워커가 동시에 작업을 처리
- **메시지 브로커**: Redis, RabbitMQ 등을 통해 작업 큐 관리
- **확장성**: 워커 수를 동적으로 조정 가능
- **모니터링**: Flower를 통한 실시간 모니터링

## 🏗️ 아키텍처 이해

### 기본 구조
```
[FastAPI] → [Redis Queue] → [Celery Workers] → [Database]
    ↓           ↓              ↓
  요청 전송    작업 큐        백그라운드 처리
```

### 핵심 컴포넌트

1. **Producer (생산자)**: 작업을 큐에 전송하는 애플리케이션
2. **Broker (브로커)**: 작업을 저장하고 전달하는 메시지 큐 (Redis/RabbitMQ)
3. **Worker (워커)**: 실제 작업을 수행하는 프로세스
4. **Result Backend (결과 백엔드)**: 작업 결과를 저장하는 저장소

## 🔧 기본 사용법

### 1. Celery 애플리케이션 생성

```python
from celery import Celery

# Celery 앱 생성
app = Celery('myapp')

# 브로커 설정
app.conf.broker_url = 'redis://localhost:6379/0'
app.conf.result_backend = 'redis://localhost:6379/0'
```

### 2. 태스크 정의

```python
@app.task
def add(x, y):
    return x + y

@app.task(bind=True)
def long_running_task(self):
    # 진행률 업데이트
    self.update_state(state='PROGRESS', meta={'progress': 50})
    # 작업 수행
    return '완료'
```

### 3. 태스크 실행

```python
# 비동기 실행
result = add.delay(4, 4)

# 결과 확인
print(result.get())  # 8

# 상태 확인
print(result.status)  # SUCCESS
```

## 📚 고급 기능

### 큐 라우팅

```python
# 큐별 라우팅 설정
app.conf.task_routes = {
    'tasks.heavy_task': {'queue': 'heavy'},
    'tasks.light_task': {'queue': 'light'},
}
```

### 재시도 및 타임아웃

```python
@app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3})
def unreliable_task(self):
    # 실패 시 자동 재시도
    pass
```

### 주기적 작업 (Celery Beat)

```python
from celery.schedules import crontab

app.conf.beat_schedule = {
    'daily-cleanup': {
        'task': 'tasks.cleanup',
        'schedule': crontab(hour=0, minute=0),  # 매일 자정
    },
}
```

## 🐳 Docker 환경에서의 Celery

### Docker Compose 설정

```yaml
services:
  celery-worker:
    build: ./backend
    command: celery -A app.celery_app worker --loglevel=info
    environment:
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis

  celery-beat:
    build: ./backend
    command: celery -A app.celery_app beat --loglevel=info
    depends_on:
      - redis

  celery-flower:
    build: ./backend
    command: celery -A app.celery_app flower --port=5555
    ports:
      - "5555:5555"
```

## 📊 모니터링 및 디버깅

### Flower 웹 인터페이스

- **URL**: http://localhost:5555
- **기능**: 워커 상태, 태스크 모니터링, 큐 상태 확인

### 로깅 설정

```python
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.task
def my_task():
    logger.info("태스크 시작")
    # 작업 수행
    logger.info("태스크 완료")
```

## ⚡ 성능 최적화

### 워커 설정

```python
# 워커 최적화 설정
app.conf.update(
    worker_prefetch_multiplier=1,  # 한 번에 하나의 작업만 처리
    worker_max_tasks_per_child=1000,  # 1000개 작업 후 워커 재시작
    task_acks_late=True,  # 작업 완료 후 ACK
)
```

### 큐 분리

```python
# 작업 유형별 큐 분리
app.conf.task_routes = {
    'heavy_tasks.*': {'queue': 'heavy'},
    'light_tasks.*': {'queue': 'light'},
    'urgent_tasks.*': {'queue': 'urgent'},
}
```

## 🚨 에러 처리

### 태스크 실패 처리

```python
@app.task(bind=True)
def risky_task(self):
    try:
        # 위험한 작업
        pass
    except Exception as exc:
        # 실패 시 상태 업데이트
        self.update_state(
            state='FAILURE',
            meta={'error': str(exc)}
        )
        raise
```

### 재시도 전략

```python
@app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def retry_task(self):
    # 실패 시 60초 후 재시도, 최대 3회
    pass
```

## 🔍 디버깅 팁

### 일반적인 문제들

1. **브로커 연결 실패**: Redis/RabbitMQ 서비스 확인
2. **워커가 작업을 받지 못함**: 큐 이름 및 라우팅 확인
3. **메모리 누수**: 워커 재시작 주기 조정
4. **태스크 타임아웃**: 타임아웃 설정 조정

### 디버깅 명령어

```bash
# 워커 상태 확인
celery -A app.celery_app inspect active

# 큐 상태 확인
celery -A app.celery_app inspect stats

# 등록된 태스크 확인
celery -A app.celery_app inspect registered
```

---

## 🏢 Company-on 프로젝트 적용 사례

### 프로젝트에서의 Celery 활용

우리 Company-on 프로젝트에서는 다음과 같이 Celery를 활용했습니다:

#### 1. 문서 처리 파이프라인 자동화

**문제**: 대용량 PDF/DOCX 파일 처리가 시간이 오래 걸려 사용자 경험 저하
**해결**: Celery를 사용한 백그라운드 처리

```python
# 문서 처리 태스크
@celery_app.task(bind=True, name="process_document_pipeline")
def process_document_pipeline_task(self, upload_id: str):
    # 1. 파일 다운로드
    # 2. 텍스트 추출
    # 3. 텍스트 청킹
    # 4. 임베딩 생성
    # 5. 벡터 DB 저장
    # 각 단계별 진행률 업데이트 및 SSE 알림
```

#### 2. 큐 분리 전략

```python
# 작업 유형별 큐 분리
task_routes={
    "app.tasks.document_processing_tasks.*": {"queue": "document_processing"},
    "app.tasks.chat_tasks.*": {"queue": "chat_processing"},
}
```

**장점**:
- 문서 처리와 채팅 처리를 독립적으로 관리
- 워커 리소스 최적화
- 장애 격리

#### 3. 실시간 상태 추적

```python
# 태스크 진행률 업데이트
self.update_state(
    state="PROGRESS",
    meta={
        "upload_id": upload_id,
        "status": "processing",
        "message": "텍스트 추출 완료",
        "progress": 50
    }
)

# SSE로 실시간 알림
await sse_service.broadcast_upload_status_change(
    upload_id, "processing", progress, total, message
)
```

#### 4. 에러 처리 및 재시도

```python
@celery_app.task(bind=True, name="retry_document_processing")
def retry_document_processing_task(self, upload_id: str):
    # 실패한 문서 처리 재시도
    # 기존 태스크 취소 후 새 태스크 시작
```

#### 5. 주기적 정리 작업

```python
# 매일 자정에 오래된 세션 정리
celery_app.conf.beat_schedule = {
    "cleanup-old-sessions": {
        "task": "app.tasks.cleanup_tasks.cleanup_old_sessions",
        "schedule": 86400.0,  # 24시간
    },
}
```

### Docker Compose 설정

```yaml
# Celery 워커
celery-worker:
  command: celery -A app.celery_app worker --loglevel=info --queues=document_processing,chat_processing,default

# Celery Beat (스케줄러)
celery-beat:
  command: celery -A app.celery_app beat --loglevel=info

# Celery Flower (모니터링)
celery-flower:
  command: celery -A app.celery_app flower --port=5555
  ports:
    - "5555:5555"
```

### API 통합

```python
# FastAPI에서 Celery 태스크 호출
@router.post("/start/{upload_id}")
async def start_document_processing(upload_id: str):
    # Celery 태스크로 백그라운드 처리
    task = process_document_pipeline_task.delay(upload_id)
    
    return {
        "message": "Document processing started",
        "upload_id": upload_id,
        "task_id": task.id  # 태스크 추적용 ID
    }
```

### 모니터링 및 디버깅

- **Flower**: http://localhost:5555에서 실시간 모니터링
- **로그**: 각 워커별 상세 로그 확인
- **상태 추적**: 태스크 ID로 진행 상황 추적

### 성능 최적화 결과

1. **사용자 경험**: 문서 업로드 후 즉시 응답, 백그라운드에서 처리
2. **확장성**: 워커 수 조정으로 처리 용량 확장
3. **안정성**: 실패한 작업 자동 재시도
4. **모니터링**: 실시간 상태 추적 및 알림

### 학습 포인트

1. **비동기 처리의 중요성**: 사용자 경험 향상
2. **큐 분리 전략**: 작업 유형별 독립적 관리
3. **상태 추적**: 실시간 진행률 및 에러 알림
4. **에러 처리**: 재시도 및 복구 전략
5. **모니터링**: Flower를 통한 실시간 모니터링

이러한 Celery 활용을 통해 Company-on 프로젝트는 대용량 문서 처리도 사용자 경험을 해치지 않고 안정적으로 처리할 수 있게 되었습니다.
