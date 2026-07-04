"""Like business logic.

Likes are written straight to PostgreSQL (the unique constraint guarantees
one like per user per post). Redis only *caches* the like count for fast reads.
"""

import uuid

from fastapi import HTTPException, status
from redis.asyncio import Redis

from app.models.like import Like
from app.models.user import User
from app.repositories.like_repository import LikeRepository
from app.repositories.post_repository import PostRepository
from app.schemas.like import LikeStatus

_LIKE_COUNT_KEY = "post:{post_id}:likes_count"


class LikeService:
    def __init__(
        self,
        likes: LikeRepository,
        posts: PostRepository,
        redis: Redis,
    ) -> None:
        self.likes = likes
        self.posts = posts
        self.redis = redis

    async def like(self, post_id: uuid.UUID, user: User) -> LikeStatus:
        post = await self._get_post_or_404(post_id)
        if post.author_id == user.id:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, "You cannot like your own post"
            )
        if await self.likes.exists(user.id, post_id):
            raise HTTPException(
                status.HTTP_409_CONFLICT, "You have already liked this post"
            )
        await self.likes.create(Like(user_id=user.id, post_id=post_id))
        count = await self._recount(post_id)
        return LikeStatus(post_id=post_id, likes_count=count, liked=True)

    async def unlike(self, post_id: uuid.UUID, user: User) -> LikeStatus:
        await self._get_post_or_404(post_id)
        like = await self.likes.get(user.id, post_id)
        if like is None:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, "You have not liked this post"
            )
        await self.likes.delete(like)
        count = await self._recount(post_id)
        return LikeStatus(post_id=post_id, likes_count=count, liked=False)

    async def get_count(self, post_id: uuid.UUID) -> int:
        """Cache-aside read: try Redis first, fall back to the database."""
        cached = await self.redis.get(_LIKE_COUNT_KEY.format(post_id=post_id))
        if cached is not None:
            return int(cached)
        count = await self.likes.count_for_post(post_id)
        await self.redis.set(_LIKE_COUNT_KEY.format(post_id=post_id), count)
        return count

    async def liked_by(self, post_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        return await self.likes.exists(user_id, post_id)

    async def _recount(self, post_id: uuid.UUID) -> int:
        count = await self.likes.count_for_post(post_id)
        await self.redis.set(_LIKE_COUNT_KEY.format(post_id=post_id), count)
        return count

    async def _get_post_or_404(self, post_id: uuid.UUID):
        post = await self.posts.get_by_id(post_id)
        if post is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found")
        return post
