"""Periodic task: remove stale unverified users."""

import logging

from app.core.config import settings
from app.services.maintenance import delete_unverified_users
from app.tasks.celery_app import celery_app
from app.tasks.sync_db import SyncSessionLocal

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.cleanup.cleanup_unverified_users")
def cleanup_unverified_users() -> int:
    """Delete users still unverified past the configured TTL. Returns count."""
    with SyncSessionLocal() as session:
        deleted = delete_unverified_users(session, settings.unverified_user_ttl_hours)
    logger.info("cleanup_unverified_users: deleted %s user(s)", deleted)
    return deleted
