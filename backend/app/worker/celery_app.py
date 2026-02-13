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
    worker_send_task_events=True,
    task_send_sent_event=True,
    task_routes={
        "app.worker.tasks.poll.*": {"queue": "poll"},
        "app.worker.tasks.process.process_episode": {"queue": "process"},
        "app.worker.tasks.process.download_episode_audio": {"queue": "download"},
        "app.worker.tasks.process.transcribe_episode_audio": {"queue": "transcription"},
        "app.worker.tasks.process.detect_episode_keywords": {"queue": "keywords"},
        "app.worker.tasks.process.enrich_episode_mentions": {"queue": "llm"},
    },
    beat_schedule={
        "poll-all-feeds": {
            "task": "app.worker.tasks.poll.poll_all_feeds",
            "schedule": crontab(minute="*/15"),
        },
    },
)
