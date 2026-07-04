"""User-profile endpoints."""

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, get_user_repository
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserRead, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.patch("/me", response_model=UserRead)
async def update_me(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    users: UserRepository = Depends(get_user_repository),
) -> User:
    """Update the current user's profile (username / full_name)."""
    return await UserService(users).update_profile(current_user, data)
