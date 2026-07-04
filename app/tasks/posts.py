"""Periodic task: remove posts older than the configured lifetime (Bonus)."""

import logging

from app.core.config import settings
from app.services.maintenance import delete_old_posts
from app.tasks.celery_app import celery_app
from app.tasks.sync_db import SyncSessionLocal

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.posts.cleanup_old_posts")
def cleanup_old_posts() -> int:
    """Delete posts older than POST_TTL_DAYS. Returns count."""
    with SyncSessionLocal() as session:
        deleted = delete_old_posts(session, settings.post_ttl_days)
    logger.info("cleanup_old_posts: deleted %s post(s)", deleted)
    return deleted
