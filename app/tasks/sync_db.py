"""Synchronous SQLAlchemy engine/session for Celery tasks.

The web app uses async SQLAlchemy, but Celery workers are synchronous, so tasks
use a separate sync engine (psycopg2) to avoid event-loop complications.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# Reuse the same database, but with the synchronous psycopg2 driver.
sync_database_url = settings.database_url.replace("+asyncpg", "+psycopg2")

sync_engine = create_engine(sync_database_url, future=True, pool_pre_ping=True)
SyncSessionLocal = sessionmaker(
    bind=sync_engine, class_=Session, expire_on_commit=False
)
