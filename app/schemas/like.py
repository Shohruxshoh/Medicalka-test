"""Like schemas."""

import uuid

from pydantic import BaseModel


class LikeStatus(BaseModel):
    """Returned after liking / unliking, with the fresh like count."""

    post_id: uuid.UUID
    likes_count: int
    liked: bool
