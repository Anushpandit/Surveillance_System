"""Database operations for users and password reset flows."""

import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from backend.auth.models import UserModel, UserRole
from backend.auth.security import hash_password, verify_password
from backend.config import settings


def get_user_by_username(db: Session, username: str) -> UserModel | None:
    """Find a user by username."""
    return db.query(UserModel).filter(UserModel.username == username).first()


def get_user_by_email(db: Session, email: str) -> UserModel | None:
    """Find a user by email address."""
    return db.query(UserModel).filter(UserModel.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> UserModel | None:
    """Find a user by primary key."""
    return db.query(UserModel).filter(UserModel.id == user_id).first()


def create_user(
    db: Session,
    username: str,
    email: str,
    password: str,
    role: UserRole = UserRole.VIEWER,
) -> UserModel:
    """Create a user, rejecting duplicate usernames and email addresses."""
    if get_user_by_username(db, username):
        raise ValueError("Username already taken")
    if get_user_by_email(db, email):
        raise ValueError("Email already registered")

    user = UserModel(
        username=username,
        email=email,
        hashed_password=hash_password(password),
        role=role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, username: str, password: str) -> UserModel | None:
    """Authenticate without revealing whether the username exists."""
    user = get_user_by_username(db, username)
    if user is None or not user.is_active:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def set_user_role(db: Session, user_id: int, role: UserRole) -> UserModel | None:
    """Set a user's role."""
    user = get_user_by_id(db, user_id)
    if user is None:
        return None
    user.role = role
    db.commit()
    db.refresh(user)
    return user


def deactivate_user(db: Session, user_id: int) -> UserModel | None:
    """Deactivate a user without deleting their audit identity."""
    user = get_user_by_id(db, user_id)
    if user is None:
        return None
    user.is_active = False
    db.commit()
    db.refresh(user)
    return user


def create_password_reset_token(db: Session, email: str) -> str | None:
    """Create a time-limited reset token, or ``None`` for unknown email."""
    user = get_user_by_email(db, email)
    if user is None:
        return None

    token = secrets.token_urlsafe(32)
    user.reset_token = token
    user.reset_token_expires = datetime.now(timezone.utc) + timedelta(
        minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES
    )
    db.commit()
    return token


def reset_password_with_token(db: Session, token: str, new_password: str) -> bool:
    """Reset a password once when the token is valid and unexpired."""
    user = db.query(UserModel).filter(UserModel.reset_token == token).first()
    if user is None or user.reset_token_expires is None:
        return False

    expires = user.reset_token_expires
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires < datetime.now(timezone.utc):
        return False

    user.hashed_password = hash_password(new_password)
    user.reset_token = None
    user.reset_token_expires = None
    db.commit()
    return True
