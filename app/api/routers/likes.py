"""Like endpoints (nested under a post)."""

import uuid

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, get_like_service
from app.models.user import User
from app.schemas.like import LikeStatus
from app.services.like_service import LikeService

router = APIRouter(prefix="/posts", tags=["likes"])


@router.post("/{post_id}/like", response_model=LikeStatus)
async def like_post(
    post_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: LikeService = Depends(get_like_service),
) -> LikeStatus:
    """Like a post. Allowed for any logged-in user (even unverified)."""
    return await service.like(post_id, current_user)


@router.delete("/{post_id}/like", response_model=LikeStatus)
async def unlike_post(
    post_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: LikeService = Depends(get_like_service),
) -> LikeStatus:
    """Remove your like from a post."""
    return await service.unlike(post_id, current_user)
