"""Authentication business logic."""

from fastapi import HTTPException, status

from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate


class AuthService:
    def __init__(self, users: UserRepository) -> None:
        self.users = users

    async def register(self, data: UserCreate) -> User:
        """Create a new (unverified) user, rejecting duplicates."""
        if await self.users.get_by_email(data.email):
            raise HTTPException(status.HTTP_409_CONFLICT, "Email is already registered")
        if await self.users.get_by_username(data.username):
            raise HTTPException(status.HTTP_409_CONFLICT, "Username is already taken")

        user = User(
            email=data.email,
            username=data.username,
            full_name=data.full_name,
            password_hash=hash_password(data.password),
            is_verified=False,
        )
        return await self.users.create(user)

    async def authenticate(self, login: str, password: str) -> User:
        """Verify credentials; `login` may be an email or a username."""
        user = await self.users.get_by_email(login)
        if user is None:
            user = await self.users.get_by_username(login)
        if user is None or not verify_password(password, user.password_hash):
            raise HTTPException(
                status.HTTP_401_UNAUTHORIZED,
                "Incorrect email/username or password",
            )
        return user

    @staticmethod
    def create_token(user: User) -> str:
        return create_access_token(subject=str(user.id))
