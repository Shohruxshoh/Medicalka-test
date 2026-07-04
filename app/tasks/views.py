"""Periodic task: flush buffered view counts from Redis into PostgreSQL."""

import logging
import uuid

from sqlalchemy import update

from app.models.post import Post
from app.services.view_service import DIRTY_POSTS_KEY, view_count_key
from app.tasks.celery_app import celery_app
from app.tasks.sync_db import SyncSessionLocal
from app.tasks.sync_redis import sync_redis

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.views.flush_views")
def flush_views() -> int:
    """Move each dirty post's buffered views from Redis into the DB.

    Returns the total number of views flushed.
    """
    post_ids = sync_redis.smembers(DIRTY_POSTS_KEY)
    if not post_ids:
        return 0

    flushed_total = 0
    with SyncSessionLocal() as session:
        for post_id in post_ids:
            # Clear the dirty flag first, then atomically read+delete the counter.
            # A view arriving in-between simply re-adds the post to the set.
            sync_redis.srem(DIRTY_POSTS_KEY, post_id)
            delta_raw = sync_redis.getdel(view_count_key(post_id))
            delta = int(delta_raw) if delta_raw else 0
            if delta == 0:
                continue
            session.execute(
                update(Post)
                .where(Post.id == uuid.UUID(post_id))
                .values(views=Post.views + delta)
            )
            flushed_total += delta
        session.commit()

    if flushed_total:
        logger.info("flush_views: flushed %s view(s)", flushed_total)
    return flushed_total
