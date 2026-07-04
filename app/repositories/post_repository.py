"""Data-access layer for the Post model."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.post import Post


class PostRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, post: Post) -> Post:
        self.session.add(post)
        await self.session.commit()
        await self.session.refresh(post)
        return post

    async def get_by_id(self, post_id: uuid.UUID) -> Post | None:
        return await self.session.get(Post, post_id)

    async def save(self, post: Post) -> Post:
        await self.session.commit()
        await self.session.refresh(post)
        return post

    async def delete(self, post: Post) -> None:
        await self.session.delete(post)
        await self.session.commit()

    @staticmethod
    def _apply_filters(
        stmt: Select,
        search: str | None,
        date_from: datetime | None,
        date_to: datetime | None,
    ) -> Select:
        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(
                or_(Post.title.ilike(pattern), Post.content.ilike(pattern))
            )
        if date_from is not None:
            stmt = stmt.where(Post.created_at >= date_from)
        if date_to is not None:
            stmt = stmt.where(Post.created_at <= date_to)
        return stmt

    async def list(
        self,
        limit: int,
        offset: int,
        search: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> list[Post]:
        stmt = self._apply_filters(select(Post), search, date_from, date_to)
        stmt = stmt.order_by(Post.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count(
        self,
        search: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> int:
        stmt = self._apply_filters(
            select(func.count()).select_from(Post), search, date_from, date_to
        )
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def list_for_authors(self, author_ids: list[uuid.UUID]) -> list[Post]:
        if not author_ids:
            return []
        result = await self.session.execute(
            select(Post)
            .where(Post.author_id.in_(author_ids))
            .order_by(Post.created_at.desc())
        )
        return list(result.scalars().all())
