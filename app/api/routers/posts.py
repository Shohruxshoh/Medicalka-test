"""Post endpoints (CRUD + view counting)."""

import uuid

from fastapi import APIRouter, Depends, status

from app.api.deps import (
    get_comment_service,
    get_current_user,
    get_current_verified_user,
    get_like_service,
    get_post_service,
)
from app.models.user import User
from app.schemas.pagination import Page, PaginationParams
from app.schemas.post import (
    PostCreate,
    PostDetail,
    PostFilterParams,
    PostRead,
    PostUpdate,
)
from app.services.comment_service import CommentService
from app.services.like_service import LikeService
from app.services.post_service import PostService

router = APIRouter(prefix="/posts", tags=["posts"])


@router.get("", response_model=Page[PostRead])
async def list_posts(
    pagination: PaginationParams = Depends(),
    filters: PostFilterParams = Depends(),
    _: User = Depends(get_current_user),
    service: PostService = Depends(get_post_service),
) -> Page[PostRead]:
    """List posts (paginated) with optional search & date filters."""
    return await service.list(pagination, filters)


@router.post("", response_model=PostRead, status_code=status.HTTP_201_CREATED)
async def create_post(
    data: PostCreate,
    current_user: User = Depends(get_current_verified_user),
    service: PostService = Depends(get_post_service),
) -> PostRead:
    """Create a post. Requires a verified account."""
    return await service.create(current_user, data)


@router.get("/{post_id}", response_model=PostDetail)
async def get_post(
    post_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    posts: PostService = Depends(get_post_service),
    comments: CommentService = Depends(get_comment_service),
    likes: LikeService = Depends(get_like_service),
) -> PostDetail:
    """Read a single post with its comments and likes (registers a view)."""
    post = await posts.get(post_id, current_user.id)
    comment_list = await comments.list_for_post(post_id)
    likes_count = await likes.get_count(post_id)
    liked_by_me = await likes.liked_by(post_id, current_user.id)
    return PostDetail(
        **post.model_dump(),
        likes_count=likes_count,
        liked_by_me=liked_by_me,
        comments=comment_list,
    )


@router.patch("/{post_id}", response_model=PostRead)
async def update_post(
    post_id: uuid.UUID,
    data: PostUpdate,
    current_user: User = Depends(get_current_verified_user),
    service: PostService = Depends(get_post_service),
) -> PostRead:
    """Update a post. Only its author may do this."""
    return await service.update(post_id, current_user, data)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: uuid.UUID,
    current_user: User = Depends(get_current_verified_user),
    service: PostService = Depends(get_post_service),
) -> None:
    """Delete a post. Only its author may do this."""
    await service.delete(post_id, current_user)
