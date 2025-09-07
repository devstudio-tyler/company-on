"""
Celery 애플리케이션 설정
백그라운드 작업을 위한 Celery 설정
"""
import os
from celery import Celery
from celery.signals import worker_ready, worker_shutdown
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Redis URL 설정
redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")

# Celery 애플리케이션 생성
celery_app = Celery(
    "company_on_worker",
    broker=redis_url,
    backend=redis_url,
    include=[
        "app.tasks.document_processing_tasks",
        "app.tasks.chat_tasks"
    ]
)

# Celery 설정
celery_app.conf.update(
    # 작업 설정
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # 작업 실행 설정
    task_always_eager=False,  # 실제 비동기 실행
    task_eager_propagates=True,
    
    # 결과 백엔드 설정
    result_expires=3600,  # 1시간 후 결과 만료
    result_persistent=True,
    
    # 워커 설정
    worker_prefetch_multiplier=1,  # 한 번에 하나의 작업만 처리
    worker_max_tasks_per_child=1000,  # 1000개 작업 후 워커 재시작
    
    # 재시도 설정
    task_acks_late=True,
    worker_disable_rate_limits=False,
    
    # 타임아웃 설정
    task_soft_time_limit=300,  # 5분 소프트 타임아웃
    task_time_limit=600,  # 10분 하드 타임아웃
    
    # 라우팅 설정
    task_routes={
        "app.tasks.document_processing_tasks.*": {"queue": "document_processing"},
        "app.tasks.chat_tasks.*": {"queue": "chat_processing"},
    },
    
    # 큐 설정
    task_default_queue="default",
    task_queues={
        "default": {
            "exchange": "default",
            "exchange_type": "direct",
            "routing_key": "default",
        },
        "document_processing": {
            "exchange": "document_processing",
            "exchange_type": "direct",
            "routing_key": "document_processing",
        },
        "chat_processing": {
            "exchange": "chat_processing",
            "exchange_type": "direct",
            "routing_key": "chat_processing",
        },
    },
    
    # 모니터링 설정
    worker_send_task_events=True,
    task_send_sent_event=True,
)

# 워커 시작/종료 시그널
@worker_ready.connect
def worker_ready_handler(sender=None, **kwargs):
    """워커 시작 시 실행"""
    logger.info(f"Celery worker {sender} is ready")

@worker_shutdown.connect
def worker_shutdown_handler(sender=None, **kwargs):
    """워커 종료 시 실행"""
    logger.info(f"Celery worker {sender} is shutting down")

# 주기적 작업 설정 (향후 확장용)
celery_app.conf.beat_schedule = {
    # 예시: 매일 자정에 정리 작업
    "cleanup-old-sessions": {
        "task": "app.tasks.cleanup_tasks.cleanup_old_sessions",
        "schedule": 86400.0,  # 24시간
    },
}

# 자동 검색 설정
celery_app.autodiscover_tasks([
    "app.tasks"
])

if __name__ == "__main__":
    celery_app.start()
