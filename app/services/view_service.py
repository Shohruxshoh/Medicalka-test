"""Redis-backed view counter (write-behind buffering).

Views are incremented in Redis (fast, in-memory) and flushed to PostgreSQL
periodically by a Celery task (Stage 7). A short-lived per-viewer key prevents
the same user from inflating the count by refreshing.
"""

import uuid

from redis.asyncio import Redis

from app.core.config import settings

_COUNT_KEY = "post:{post_id}:views"
_DEDUP_KEY = "viewed:{post_id}:{viewer_id}"
DIRTY_POSTS_KEY = "dirty_posts"


def view_count_key(post_id) -> str:
    return _COUNT_KEY.format(post_id=post_id)


class ViewService:
    def __init__(self, redis: Redis) -> None:
        self.redis = redis

    async def register_view(self, post_id: uuid.UUID, viewer_id: uuid.UUID) -> None:
        """Count one view, unless this viewer viewed the post very recently."""
        dedup_key = _DEDUP_KEY.format(post_id=post_id, viewer_id=viewer_id)
        is_new = await self.redis.set(
            dedup_key, "1", ex=settings.view_dedup_ttl_seconds, nx=True
        )
        if not is_new:
            return
        await self.redis.incr(_COUNT_KEY.format(post_id=post_id))
        # Mark this post as having un-flushed views (used by the flush task).
        await self.redis.sadd(DIRTY_POSTS_KEY, str(post_id))

    async def get_buffered(self, post_id: uuid.UUID) -> int:
        value = await self.redis.get(_COUNT_KEY.format(post_id=post_id))
        return int(value) if value else 0

    async def get_buffered_many(
        self, post_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, int]:
        if not post_ids:
            return {}
        keys = [_COUNT_KEY.format(post_id=pid) for pid in post_ids]
        values = await self.redis.mget(keys)
        return {
            pid: (int(v) if v else 0) for pid, v in zip(post_ids, values, strict=False)
        }

    async def clear(self, post_id: uuid.UUID) -> None:
        """Drop a post's buffered views (called when the post is deleted)."""
        await self.redis.delete(_COUNT_KEY.format(post_id=post_id))
        await self.redis.srem(DIRTY_POSTS_KEY, str(post_id))
