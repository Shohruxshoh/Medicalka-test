"""Shared FastAPI dependencies (DB repos, current user, services)."""

import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.redis_client import redis_client
from app.core.security import decode_access_token
from app.models.user import User
from app.repositories.comment_repository import CommentRepository
from app.repositories.like_repository import LikeRepository
from app.repositories.post_repository import PostRepository
from app.repositories.user_repository import UserRepository
from app.repositories.verification_token_repository import (
    VerificationTokenRepository,
)
from app.services.comment_service import CommentService
from app.services.feed_service import FeedService
from app.services.like_service import LikeService
from app.services.post_service import PostService
from app.services.rate_limiter import RateLimiter
from app.services.view_service import ViewService

# Tells Swagger where to obtain a token and how to read the Bearer header.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


# ── Infrastructure ────────────────────────────────────────────────
def get_redis() -> Redis:
    return redis_client


# ── Repositories ──────────────────────────────────────────────────
def get_user_repository(session: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(session)


def get_verification_token_repository(
    session: AsyncSession = Depends(get_db),
) -> VerificationTokenRepository:
    return VerificationTokenRepository(session)


def get_post_repository(session: AsyncSession = Depends(get_db)) -> PostRepository:
    return PostRepository(session)


def get_comment_repository(
    session: AsyncSession = Depends(get_db),
) -> CommentRepository:
    return CommentRepository(session)


def get_like_repository(session: AsyncSession = Depends(get_db)) -> LikeRepository:
    return LikeRepository(session)


# ── Services ──────────────────────────────────────────────────────
def get_view_service(redis: Redis = Depends(get_redis)) -> ViewService:
    return ViewService(redis)


def get_post_service(
    posts: PostRepository = Depends(get_post_repository),
    views: ViewService = Depends(get_view_service),
) -> PostService:
    return PostService(posts, views)


def get_comment_service(
    comments: CommentRepository = Depends(get_comment_repository),
    posts: PostRepository = Depends(get_post_repository),
) -> CommentService:
    return CommentService(comments, posts)


def get_like_service(
    likes: LikeRepository = Depends(get_like_repository),
    posts: PostRepository = Depends(get_post_repository),
    redis: Redis = Depends(get_redis),
) -> LikeService:
    return LikeService(likes, posts, redis)


def get_feed_service(
    users: UserRepository = Depends(get_user_repository),
    posts: PostRepository = Depends(get_post_repository),
    likes: LikeRepository = Depends(get_like_repository),
) -> FeedService:
    return FeedService(users, posts, likes)


def get_login_rate_limiter(redis: Redis = Depends(get_redis)) -> RateLimiter:
    return RateLimiter(redis, settings.login_max_attempts, settings.login_block_seconds)


# ── Current user ──────────────────────────────────────────────────
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    users: UserRepository = Depends(get_user_repository),
) -> User:
    """Resolve the authenticated user from the Bearer token."""
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    subject = decode_access_token(token)
    if subject is None:
        raise credentials_error
    try:
        user_id = uuid.UUID(subject)
    except ValueError:
        raise credentials_error from None

    user = await users.get_by_id(user_id)
    if user is None:
        raise credentials_error
    return user


async def get_current_verified_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Require the authenticated user to have a verified email."""
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email is not verified",
        )
    return current_user
