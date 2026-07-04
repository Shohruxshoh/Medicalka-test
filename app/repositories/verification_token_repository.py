"""Data-access layer for the VerificationToken model."""

import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.verification_token import VerificationToken


class VerificationTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, token: VerificationToken) -> VerificationToken:
        self.session.add(token)
        await self.session.commit()
        await self.session.refresh(token)
        return token

    async def get_by_token(self, token_str: str) -> VerificationToken | None:
        result = await self.session.execute(
            select(VerificationToken).where(VerificationToken.token == token_str)
        )
        return result.scalar_one_or_none()

    async def delete(self, token: VerificationToken) -> None:
        await self.session.delete(token)
        await self.session.commit()

    async def delete_for_user(self, user_id: uuid.UUID) -> None:
        """Remove all tokens belonging to a user (used before issuing a new one)."""
        await self.session.execute(
            delete(VerificationToken).where(VerificationToken.user_id == user_id)
        )
        await self.session.commit()
