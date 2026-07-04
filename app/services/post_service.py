"""Post business logic: CRUD, ownership checks, and view merging."""

import uuid

from fastapi import HTTPException, status

from app.models.post import Post
from app.models.user import User
from app.repositories.post_repository import PostRepository
from app.schemas.pagination import Page, PaginationParams
from app.schemas.post import PostCreate, PostFilterParams, PostRead, PostUpdate
from app.services.view_service import ViewService


class PostService:
    def __init__(self, posts: PostRepository, views: ViewService) -> None:
        self.posts = posts
        self.views = views

    async def create(self, author: User, data: PostCreate) -> PostRead:
        post = Post(author_id=author.id, title=data.title, content=data.content)
        post = await self.posts.create(post)
        return self._to_read(post, 0)

    async def get(self, post_id: uuid.UUID, viewer_id: uuid.UUID) -> PostRead:
        post = await self._get_or_404(post_id)
        # Viewing the detail page counts as a view (buffered in Redis).
        await self.views.register_view(post_id, viewer_id)
        buffered = await self.views.get_buffered(post_id)
        return self._to_read(post, buffered)

    async def list(
        self, pagination: PaginationParams, filters: PostFilterParams
    ) -> Page[PostRead]:
        filter_args = {
            "search": filters.search,
            "date_from": filters.date_from,
            "date_to": filters.date_to,
        }
        posts = await self.posts.list(
            limit=pagination.limit, offset=pagination.offset, **filter_args
        )
        total = await self.posts.count(**filter_args)
        buffered = await self.views.get_buffered_many([p.id for p in posts])
        items = [self._to_read(p, buffered.get(p.id, 0)) for p in posts]
        pages = (total + pagination.page_size - 1) // pagination.page_size
        return Page[PostRead](
            items=items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            pages=pages,
        )

    async def update(
        self, post_id: uuid.UUID, user: User, data: PostUpdate
    ) -> PostRead:
        post = await self._get_or_404(post_id)
        self._ensure_owner(post, user)
        if data.title is not None:
            post.title = data.title
        if data.content is not None:
            post.content = data.content
        post = await self.posts.save(post)
        buffered = await self.views.get_buffered(post_id)
        return self._to_read(post, buffered)

    async def delete(self, post_id: uuid.UUID, user: User) -> None:
        post = await self._get_or_404(post_id)
        self._ensure_owner(post, user)
        await self.posts.delete(post)
        await self.views.clear(post_id)

    async def _get_or_404(self, post_id: uuid.UUID) -> Post:
        post = await self.posts.get_by_id(post_id)
        if post is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found")
        return post

    @staticmethod
    def _ensure_owner(post: Post, user: User) -> None:
        if post.author_id != user.id:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, "You can modify only your own posts"
            )

    @staticmethod
    def _to_read(post: Post, buffered_views: int) -> PostRead:
        # Total views = persisted (DB) + un-flushed (Redis buffer).
        return PostRead(
            id=post.id,
            author_id=post.author_id,
            title=post.title,
            content=post.content,
            views=post.views + buffered_views,
            created_at=post.created_at,
            updated_at=post.updated_at,
        )
