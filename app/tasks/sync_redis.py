"""Synchronous Redis client for Celery tasks."""

import redis

from app.core.config import settings

sync_redis = redis.Redis.from_url(settings.redis_url, decode_responses=True)
