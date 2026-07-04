"""Authentication & email-verification endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import (
    get_current_user,
    get_login_rate_limiter,
    get_user_repository,
    get_verification_token_repository,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.repositories.verification_token_repository import (
    VerificationTokenRepository,
)
from app.schemas.auth import Token
from app.schemas.user import UserCreate, UserRead
from app.schemas.verification import MessageResponse, VerificationRequest
from app.services.auth_service import AuthService
from app.services.rate_limiter import RateLimiter
from app.services.verification_service import VerificationService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    data: UserCreate,
    users: UserRepository = Depends(get_user_repository),
    tokens: VerificationTokenRepository = Depends(get_verification_token_repository),
) -> User:
    """Register a new (unverified) user and issue an email-verification token."""
    user = await AuthService(users).register(data)
    await VerificationService(tokens, users).generate_for_user(user)
    return user


@router.post("/login", response_model=Token)
async def login(
    request: Request,
    form: OAuth2PasswordRequestForm = Depends(),
    users: UserRepository = Depends(get_user_repository),
    limiter: RateLimiter = Depends(get_login_rate_limiter),
) -> Token:
    """Log in with email/username + password, returning a JWT.

    Repeated failures from the same client/identity are rate-limited (429).
    """
    client_ip = request.client.host if request.client else "unknown"
    key = f"login_attempts:{client_ip}:{form.username}"
    await limiter.ensure_allowed(key)

    service = AuthService(users)
    try:
        user = await service.authenticate(form.username, form.password)
    except HTTPException:
        await limiter.register_failure(key)
        raise
    await limiter.reset(key)
    return Token(access_token=service.create_token(user))


@router.get("/me", response_model=UserRead)
async def read_me(current_user: User = Depends(get_current_user)) -> User:
    """Return the currently authenticated user."""
    return current_user


@router.post("/request-verification", response_model=MessageResponse)
async def request_verification(
    payload: VerificationRequest,
    users: UserRepository = Depends(get_user_repository),
    tokens: VerificationTokenRepository = Depends(get_verification_token_repository),
) -> MessageResponse:
    """(Re)issue a verification token for the given email (simplified, no SMTP)."""
    user = await users.get_by_email(payload.email)
    if user is None or user.is_verified:
        # Generic response — do not reveal whether the email exists / is verified.
        return MessageResponse(
            detail="If that email exists and is unverified, a link was sent."
        )
    token = await VerificationService(tokens, users).generate_for_user(user)
    return MessageResponse(
        detail="Verification link sent (also logged on the server).",
        verification_token=token.token,
    )


@router.get("/verify-email", response_model=UserRead)
async def verify_email(
    token: str,
    users: UserRepository = Depends(get_user_repository),
    tokens: VerificationTokenRepository = Depends(get_verification_token_repository),
) -> User:
    """Verify an email using the token from the verification link."""
    return await VerificationService(tokens, users).verify(token)
