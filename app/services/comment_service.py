"""Comment business logic: create / list / delete with ownership checks."""

import uuid

from fastapi import HTTPException, status

from app.models.comment import Comment
from app.models.user import User
from app.repositories.comment_repository import CommentRepository
from app.repositories.post_repository import PostRepository
from app.schemas.comment import CommentCreate, CommentRead


class CommentService:
    def __init__(self, comments: CommentRepository, posts: PostRepository) -> None:
        self.comments = comments
        self.posts = posts

    async def add(
        self, post_id: uuid.UUID, author: User, data: CommentCreate
    ) -> CommentRead:
        await self._ensure_post(post_id)
        comment = Comment(post_id=post_id, author_id=author.id, content=data.content)
        comment = await self.comments.create(comment)
        return CommentRead.model_validate(comment)

    async def list_for_post(self, post_id: uuid.UUID) -> list[CommentRead]:
        await self._ensure_post(post_id)
        rows = await self.comments.list_for_post(post_id)
        return [CommentRead.model_validate(row) for row in rows]

    async def delete(
        self, post_id: uuid.UUID, comment_id: uuid.UUID, user: User
    ) -> None:
        comment = await self.comments.get_by_id(comment_id)
        if comment is None or comment.post_id != post_id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Comment not found")
        if comment.author_id != user.id:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                "You can delete only your own comments",
            )
        await self.comments.delete(comment)

    async def _ensure_post(self, post_id: uuid.UUID) -> None:
        if await self.posts.get_by_id(post_id) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found")
