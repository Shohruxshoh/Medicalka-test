"""Post schemas."""

import uuid
from datetime import datetime

from fastapi import Query
from pydantic import BaseModel, Field

from app.schemas.comment import CommentRead


class PostCreate(BaseModel):
    title: str = Field(min_length=5, max_length=255)
    content: str = Field(min_length=1, max_length=10_000)


class PostUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=5, max_length=255)
    content: str | None = Field(default=None, min_length=1, max_length=10_000)


class PostRead(BaseModel):
    id: uuid.UUID
    author_id: uuid.UUID
    title: str
    content: str
    views: int
    created_at: datetime
    updated_at: datetime


class PostDetail(PostRead):
    """Single-post view: base fields plus likes and comments."""

    likes_count: int
    liked_by_me: bool
    comments: list[CommentRead]


class PostFilterParams:
    """Optional search & date filters for the post list endpoint."""

    def __init__(
        self,
        search: str | None = Query(
            None, description="case-insensitive search in title/content"
        ),
        date_from: datetime | None = Query(
            None, description="only posts created at/after this ISO datetime"
        ),
        date_to: datetime | None = Query(
            None, description="only posts created at/before this ISO datetime"
        ),
    ) -> None:
        self.search = search
        self.date_from = date_from
        self.date_to = date_to
