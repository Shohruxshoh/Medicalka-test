"""Pydantic schemas for user input/output and validation."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

# Characters allowed in full_name in addition to letters.
_ALLOWED_NAME_EXTRA = " -'"


def _validate_full_name(value: str) -> str:
    cleaned = value.strip()
    if len(cleaned) < 2:
        raise ValueError("full_name is too short")
    if not all(ch.isalpha() or ch in _ALLOWED_NAME_EXTRA for ch in cleaned):
        raise ValueError(
            "full_name may contain only letters, spaces, hyphens and apostrophes"
        )
    return cleaned


class UserCreate(BaseModel):
    """Registration input."""

    email: EmailStr
    username: str = Field(min_length=3, max_length=32, pattern=r"^[A-Za-z0-9_]+$")
    full_name: str = Field(min_length=2, max_length=100)
    password: str = Field(min_length=8, max_length=72)

    @field_validator("full_name")
    @classmethod
    def check_full_name(cls, v: str) -> str:
        return _validate_full_name(v)


class UserUpdate(BaseModel):
    """Profile update input (every field optional)."""

    username: str | None = Field(
        default=None, min_length=3, max_length=32, pattern=r"^[A-Za-z0-9_]+$"
    )
    full_name: str | None = Field(default=None, min_length=2, max_length=100)

    @field_validator("full_name")
    @classmethod
    def check_full_name(cls, v: str | None) -> str | None:
        return None if v is None else _validate_full_name(v)


class UserRead(BaseModel):
    """Public user representation — never includes the password."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    username: str
    full_name: str
    is_verified: bool
    created_at: datetime
