"""Synchronous maintenance operations used by Celery tasks.

Kept as plain functions taking a Session so they can be unit-tested directly,
without going through Celery.
"""

from datetime import UTC, datetime, timedelta

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.models.post import Post
from app.models.user import User


def delete_unverified_users(session: Session, ttl_hours: int) -> int:
    """Delete users that are still unverified and older than ``ttl_hours``."""
    cutoff = datetime.now(UTC) - timedelta(hours=ttl_hours)
    result = session.execute(
        delete(User).where(User.is_verified.is_(False), User.created_at < cutoff)
    )
    session.commit()
    return result.rowcount


def delete_old_posts(session: Session, max_age_days: int) -> int:
    """Delete posts older than ``max_age_days``."""
    cutoff = datetime.now(UTC) - timedelta(days=max_age_days)
    result = session.execute(delete(Post).where(Post.created_at < cutoff))
    session.commit()
    return result.rowcount
