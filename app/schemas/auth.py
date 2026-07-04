"""Authentication-related schemas."""

from pydantic import BaseModel


class Token(BaseModel):
    """JWT access-token response."""

    access_token: str
    token_type: str = "bearer"
