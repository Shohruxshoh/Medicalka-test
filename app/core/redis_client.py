"""Async Redis client (shared connection pool)."""

from redis.asyncio import Redis

from app.core.config import settings

# decode_responses=True → Redis returns str instead of bytes (handy for counters).
redis_client: Redis = Redis.from_url(
    settings.redis_url,
    encoding="utf-8",
    decode_responses=True,
)
