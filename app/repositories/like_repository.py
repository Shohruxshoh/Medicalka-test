"""Data-access layer for the Like model."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.like import Like


class LikeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, user_id: uuid.UUID, post_id: uuid.UUID) -> Like | None:
        result = await self.session.execute(
            select(Like).where(Like.user_id == user_id, Like.post_id == post_id)
        )
        return result.scalar_one_or_none()

    async def exists(self, user_id: uuid.UUID, post_id: uuid.UUID) -> bool:
        result = await self.session.execute(
            select(Like.id).where(Like.user_id == user_id, Like.post_id == post_id)
        )
        return result.scalar_one_or_none() is not None

    async def create(self, like: Like) -> Like:
        self.session.add(like)
        await self.session.commit()
        await self.session.refresh(like)
        return like

    async def delete(self, like: Like) -> None:
        await self.session.delete(like)
        await self.session.commit()

    async def count_for_post(self, post_id: uuid.UUID) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(Like).where(Like.post_id == post_id)
        )
        return int(result.scalar_one())

    async def user_ids_for_posts(
        self, post_ids: list[uuid.UUID]
    ) -> list[tuple[uuid.UUID, uuid.UUID]]:
        if not post_ids:
            return []
        result = await self.session.execute(
            select(Like.post_id, Like.user_id).where(Like.post_id.in_(post_ids))
        )
        return [(row[0], row[1]) for row in result.all()]
