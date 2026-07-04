"""Pytest fixtures: an isolated test database, fake Redis, and helpers."""

import pytest
import pytest_asyncio
from fakeredis import FakeAsyncRedis, FakeServer
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session, sessionmaker

import app.models  # noqa: F401  (register all tables on Base.metadata)
from app.api.deps import get_redis
from app.core.config import settings
from app.core.database import Base, get_db
from app.main import app

_BASE_URL = settings.database_url.rsplit("/", 1)[0]
TEST_DB_URL = f"{_BASE_URL}/social_test"
SYNC_TEST_DB_URL = TEST_DB_URL.replace("+asyncpg", "+psycopg2")


@pytest.fixture(scope="session", autouse=True)
def _ensure_test_db():
    """Create the test database once (synchronously, via psycopg2)."""
    admin_url = (
        settings.database_url.replace("+asyncpg", "+psycopg2").rsplit("/", 1)[0]
        + "/postgres"
    )
    engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    with engine.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = 'social_test'")
        ).scalar()
        if not exists:
            conn.execute(text("CREATE DATABASE social_test"))
    engine.dispose()


async def _create_and_clean(engine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())


@pytest_asyncio.fixture
async def client():
    """Async client wired to a clean test DB and an isolated fake Redis."""
    engine = create_async_engine(TEST_DB_URL)
    await _create_and_clean(engine)

    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async def override_get_db():
        async with session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    fake_redis = FakeAsyncRedis(server=FakeServer(), decode_responses=True)

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = lambda: fake_redis

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
    await engine.dispose()


@pytest.fixture
def make_user(client):
    """Return a helper that registers (optionally verifies) a user and logs in.

    Usage: ``token = await make_user("a@e.com", "alice", verified=True)``
    """

    async def _make(
        email: str,
        username: str,
        *,
        verified: bool = False,
        password: str = "password123",
    ) -> str:
        await client.post(
            "/auth/register",
            json={
                "email": email,
                "username": username,
                "full_name": "Test User",
                "password": password,
            },
        )
        if verified:
            resp = await client.post(
                "/auth/request-verification", json={"email": email}
            )
            token = resp.json()["verification_token"]
            await client.get(f"/auth/verify-email?token={token}")
        login = await client.post(
            "/auth/login", data={"username": email, "password": password}
        )
        return login.json()["access_token"]

    return _make


@pytest.fixture
def sync_session():
    """A synchronous Session on the test DB (for maintenance-task unit tests)."""
    engine = create_engine(SYNC_TEST_DB_URL)
    Base.metadata.create_all(engine)
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())
    factory = sessionmaker(engine, class_=Session, expire_on_commit=False)
    session = factory()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()
