"""Async database engine, session factory, and declarative base."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# The async engine talks to PostgreSQL through the asyncpg driver.
# Creating it does NOT open a connection yet — that happens lazily.
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,  # log SQL when DEBUG=true
    future=True,
)

# Factory that produces a fresh AsyncSession per request.
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base class that all ORM models inherit from."""


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: yield one database session per request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
