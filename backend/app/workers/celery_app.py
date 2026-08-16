"""Celery app: cola de evaluación de alertas + watchdog de sin_señal."""

from celery import Celery

from ..config import get_settings

settings = get_settings()

celery_app = Celery(
    "carnetruck",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "check-missing-signal": {
            "task": "app.workers.tasks.check_missing_signal",
            "schedule": 300.0,
        },
    },
)
celery_app.autodiscover_tasks(["app.workers"])
