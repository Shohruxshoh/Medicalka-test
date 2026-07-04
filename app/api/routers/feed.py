"""Feed endpoint: users with their posts and likes (PDF 1.5)."""

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, get_feed_service
from app.models.user import User
from app.schemas.feed import FeedUser
from app.schemas.pagination import Page, PaginationParams
from app.services.feed_service import FeedService

router = APIRouter(tags=["feed"])


@router.get("/all", response_model=Page[FeedUser])
async def get_feed(
    pagination: PaginationParams = Depends(),
    _: User = Depends(get_current_user),
    service: FeedService = Depends(get_feed_service),
) -> Page[FeedUser]:
    """List users, each with their posts and the user-ids who liked them."""
    return await service.get_feed(pagination)
