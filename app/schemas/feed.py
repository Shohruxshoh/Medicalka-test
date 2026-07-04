"""Feed schemas: users with their posts and the likes on each post."""

import uuid

from pydantic import BaseModel


class FeedPost(BaseModel):
    id: uuid.UUID
    title: str
    content: str
    likes: list[uuid.UUID]  # user ids who liked this post


class FeedUser(BaseModel):
    username: str
    posts: list[FeedPost]
