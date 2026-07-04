"""User-profile business logic."""

from fastapi import HTTPException, status

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserUpdate


class UserService:
    def __init__(self, users: UserRepository) -> None:
        self.users = users

    async def update_profile(self, user: User, data: UserUpdate) -> User:
        """Update the current user's username / full_name."""
        if data.username is not None and data.username != user.username:
            existing = await self.users.get_by_username(data.username)
            if existing is not None:
                raise HTTPException(
                    status.HTTP_409_CONFLICT, "Username is already taken"
                )
            user.username = data.username

        if data.full_name is not None:
            user.full_name = data.full_name

        return await self.users.save(user)
