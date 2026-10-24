"""FastAPI dependencies for bearer authentication and admin authorization."""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.auth.crud import get_user_by_username
from backend.auth.models import UserModel, UserRole
from backend.auth.security import decode_access_token
from backend.database.database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> UserModel:
    """Resolve and validate the active user from a bearer token."""
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_error
    username = payload.get("sub")
    if username is None:
        raise credentials_error
    user = get_user_by_username(db, username)
    if user is None or not user.is_active:
        raise credentials_error
    return user


def require_admin(
    current_user: UserModel = Depends(get_current_user),
) -> UserModel:
    """Require the authenticated user to have the admin role."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This action requires admin privileges",
        )
    return current_user
