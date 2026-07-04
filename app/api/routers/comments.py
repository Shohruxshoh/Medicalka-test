"""Comment endpoints (nested under a post)."""

import uuid

from fastapi import APIRouter, Depends, status

from app.api.deps import (
    get_comment_service,
    get_current_user,
    get_current_verified_user,
)
from app.models.user import User
from app.schemas.comment import CommentCreate, CommentRead
from app.services.comment_service import CommentService

router = APIRouter(prefix="/posts", tags=["comments"])


@router.get("/{post_id}/comments", response_model=list[CommentRead])
async def list_comments(
    post_id: uuid.UUID,
    _: User = Depends(get_current_user),
    service: CommentService = Depends(get_comment_service),
) -> list[CommentRead]:
    """List all comments on a post."""
    return await service.list_for_post(post_id)


@router.post(
    "/{post_id}/comments",
    response_model=CommentRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_comment(
    post_id: uuid.UUID,
    data: CommentCreate,
    current_user: User = Depends(get_current_verified_user),
    service: CommentService = Depends(get_comment_service),
) -> CommentRead:
    """Add a comment. Requires a verified account."""
    return await service.add(post_id, current_user, data)


@router.delete(
    "/{post_id}/comments/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_comment(
    post_id: uuid.UUID,
    comment_id: uuid.UUID,
    current_user: User = Depends(get_current_verified_user),
    service: CommentService = Depends(get_comment_service),
) -> None:
    """Delete a comment. Only its author may do this."""
    await service.delete(post_id, comment_id, current_user)
