"""Unit tests for the maintenance functions used by the Celery tasks."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.models.post import Post
from app.models.user import User
from app.services.maintenance import delete_old_posts, delete_unverified_users


def _ago(**kw) -> datetime:
    return datetime.now(UTC) - timedelta(**kw)


def test_delete_unverified_users(sync_session):
    sync_session.add_all(
        [
            User(
                email="old@e.com",
                username="oldu",
                full_name="Old",
                password_hash="x",
                is_verified=False,
                created_at=_ago(hours=100),
            ),
            User(
                email="fresh@e.com",
                username="freshu",
                full_name="Fresh",
                password_hash="x",
                is_verified=False,
                created_at=_ago(hours=1),
            ),
            User(
                email="ver@e.com",
                username="veru",
                full_name="Ver",
                password_hash="x",
                is_verified=True,
                created_at=_ago(hours=100),
            ),
        ]
    )
    sync_session.commit()

    deleted = delete_unverified_users(sync_session, ttl_hours=48)

    assert deleted == 1  # only the old *and* unverified user
    usernames = set(sync_session.execute(select(User.username)).scalars().all())
    assert usernames == {"freshu", "veru"}


def test_delete_old_posts(sync_session):
    author = User(
        email="a@e.com",
        username="author",
        full_name="Author",
        password_hash="x",
        is_verified=True,
    )
    sync_session.add(author)
    sync_session.commit()

    sync_session.add_all(
        [
            Post(
                author_id=author.id,
                title="Old post title",
                content="x",
                created_at=_ago(days=40),
            ),
            Post(author_id=author.id, title="New post title", content="x"),
        ]
    )
    sync_session.commit()

    deleted = delete_old_posts(sync_session, max_age_days=30)

    assert deleted == 1
    titles = set(sync_session.execute(select(Post.title)).scalars().all())
    assert titles == {"New post title"}
