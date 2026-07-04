"""Email-verification schemas."""

from pydantic import BaseModel, EmailStr


class VerificationRequest(BaseModel):
    """Body for requesting (or resending) a verification token."""

    email: EmailStr


class MessageResponse(BaseModel):
    """Generic message.

    ``verification_token`` is returned only because this task uses no real SMTP;
    in production the token would be emailed, never returned in the response.
    """

    detail: str
    verification_token: str | None = None
