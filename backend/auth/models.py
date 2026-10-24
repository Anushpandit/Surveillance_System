"""SQLAlchemy models for users, roles, and password reset tokens."""

import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.database import Base


class UserRole(str, enum.Enum):
    """Roles supported by the surveillance dashboard."""

    ADMIN = "admin"
    VIEWER = "viewer"


class UserModel(Base):
    """Database representation of an authenticated application user."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), default=UserRole.VIEWER, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    reset_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reset_token_expires: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def to_dict(self) -> dict:
        """Return a safe public representation without password fields."""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role.value if hasattr(self.role, "value") else self.role,
            "is_active": self.is_active,
        }
