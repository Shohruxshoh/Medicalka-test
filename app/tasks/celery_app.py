"""Celery application and periodic-task schedule."""

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "social",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.cleanup", "app.tasks.views", "app.tasks.posts"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        # Move buffered view counts from Redis into PostgreSQL frequently.
        "flush-views-to-db": {
            "task": "app.tasks.views.flush_views",
            "schedule": float(settings.view_flush_interval_seconds),
        },
        # Remove stale unverified users periodically.
        "cleanup-unverified-users": {
            "task": "app.tasks.cleanup.cleanup_unverified_users",
            "schedule": 3600.0,  # every hour
        },
        # Remove posts older than the configured lifetime (Bonus).
        "cleanup-old-posts": {
            "task": "app.tasks.posts.cleanup_old_posts",
            "schedule": 86400.0,  # once a day
        },
    },
)
