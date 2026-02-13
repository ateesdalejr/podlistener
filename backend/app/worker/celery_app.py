from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery = Celery("podlistener", broker=settings.REDIS_URL)

celery.conf.update(
    include=[
        "app.worker.tasks.poll",
        "app.worker.tasks.process",
    ],
    result_backend=settings.REDIS_URL,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    task_routes={
        "app.worker.tasks.poll.*": {"queue": "poll"},
        "app.worker.tasks.process.*": {"queue": "process"},
    },
    beat_schedule={
        "poll-all-feeds": {
            "task": "app.worker.tasks.poll.poll_all_feeds",
            "schedule": crontab(minute="*/15"),
        },
    },
)
