"""Email-verification business logic (simplified — no real SMTP)."""

import logging
import secrets
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status

from app.core.config import settings
from app.models.user import User
from app.models.verification_token import VerificationToken
from app.repositories.user_repository import UserRepository
from app.repositories.verification_token_repository import (
    VerificationTokenRepository,
)

# Reuse uvicorn's logger so messages appear in the container logs.
logger = logging.getLogger("uvicorn.error")


class VerificationService:
    def __init__(
        self,
        tokens: VerificationTokenRepository,
        users: UserRepository,
    ) -> None:
        self.tokens = tokens
        self.users = users

    async def generate_for_user(self, user: User) -> VerificationToken:
        """Create a fresh verification token, replacing any previous ones."""
        await self.tokens.delete_for_user(user.id)
        token = VerificationToken(
            user_id=user.id,
            token=secrets.token_urlsafe(32),
            expires_at=(
                datetime.now(UTC)
                + timedelta(hours=settings.verification_token_expire_hours)
            ),
        )
        token = await self.tokens.create(token)
        # Simulate "sending an email" by logging the verification link.
        logger.info(
            "[email-simulation] Verify %s -> GET /auth/verify-email?token=%s",
            user.email,
            token.token,
        )
        return token

    async def verify(self, token_str: str) -> User:
        """Validate a token and mark the associated user as verified."""
        token = await self.tokens.get_by_token(token_str)
        if token is None:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "Invalid or unknown verification token",
            )
        if token.expires_at < datetime.now(UTC):
            await self.tokens.delete(token)
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "Verification token has expired",
            )

        user = await self.users.get_by_id(token.user_id)
        if user is None:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "User for this token no longer exists",
            )

        user.is_verified = True
        await self.users.save(user)
        await self.tokens.delete_for_user(user.id)
        return user
