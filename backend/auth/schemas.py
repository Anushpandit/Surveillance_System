"""Pydantic request and response schemas for authentication routes."""

from pydantic import BaseModel, EmailStr, Field

from backend.auth.models import UserRole


class UserRegister(BaseModel):
    """Public registration payload; new users always start as viewers."""

    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


class UserResponse(BaseModel):
    """Safe user representation returned by the API."""

    id: int
    username: str
    email: EmailStr
    role: str
    is_active: bool


class Token(BaseModel):
    """OAuth2 bearer token response."""

    access_token: str
    token_type: str = "bearer"


class PasswordResetRequest(BaseModel):
    """Email address requesting a password reset."""

    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Reset token and replacement password."""

    reset_token: str
    new_password: str = Field(min_length=8, max_length=72)


class RoleUpdateRequest(BaseModel):
    """Requested replacement role for an existing user."""

    role: UserRole
