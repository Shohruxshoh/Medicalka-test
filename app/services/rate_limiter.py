"""Redis-based fixed-window rate limiter (throttles login attempts)."""

from fastapi import HTTPException, status
from redis.asyncio import Redis


class RateLimiter:
    def __init__(self, redis: Redis, max_attempts: int, block_seconds: int) -> None:
        self.redis = redis
        self.max_attempts = max_attempts
        self.block_seconds = block_seconds

    async def ensure_allowed(self, key: str) -> None:
        """Raise 429 if this key has already reached the attempt limit."""
        attempts = await self.redis.get(key)
        if attempts is not None and int(attempts) >= self.max_attempts:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed login attempts. Please try again later.",
            )

    async def register_failure(self, key: str) -> None:
        """Count one failed attempt; start the expiry window on the first one."""
        count = await self.redis.incr(key)
        if count == 1:
            await self.redis.expire(key, self.block_seconds)

    async def reset(self, key: str) -> None:
        """Clear the counter (called after a successful login)."""
        await self.redis.delete(key)
