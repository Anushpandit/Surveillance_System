"""Authentication, password reset, and user administration routes."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from backend.auth import crud
from backend.auth.dependencies import get_current_user, require_admin
from backend.auth.models import UserModel
from backend.auth.schemas import (
    PasswordResetConfirm,
    PasswordResetRequest,
    RoleUpdateRequest,
    Token,
    UserRegister,
    UserResponse,
)
from backend.auth.security import create_access_token
from backend.database.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    """Register a new viewer account."""
    try:
        user = crud.create_user(db, payload.username, payload.email, payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return user.to_dict()


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Issue a bearer token for valid credentials."""
    user = crud.authenticate_user(db, form_data.username, form_data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username, "role": user.role.value})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def read_current_user(current_user: UserModel = Depends(get_current_user)):
    """Return the authenticated user's public profile."""
    return current_user.to_dict()


@router.post("/password-reset/request")
def request_password_reset(
    payload: PasswordResetRequest,
    db: Session = Depends(get_db),
):
    """Create a reset token and log it in development mode.

    A real email provider must replace the log-only delivery before production.
    """
    token = crud.create_password_reset_token(db, payload.email)
    if token:
        logger.info(
            "[PasswordReset] Token for %s: %s (development log only)",
            payload.email,
            token,
        )
    return {"message": "If an account with that email exists, a reset link has been sent."}


@router.post("/password-reset/confirm")
def confirm_password_reset(
    payload: PasswordResetConfirm,
    db: Session = Depends(get_db),
):
    """Replace a password using a valid one-time reset token."""
    if not crud.reset_password_with_token(db, payload.reset_token, payload.new_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token is invalid or has expired",
        )
    return {"message": "Password has been reset successfully."}


@router.patch("/users/{user_id}/role", response_model=UserResponse)
def update_user_role(
    user_id: int,
    payload: RoleUpdateRequest,
    db: Session = Depends(get_db),
    _admin: UserModel = Depends(require_admin),
):
    """Update a user's role; admin-only."""
    user = crud.set_user_role(db, user_id, payload.role)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user.to_dict()


@router.delete("/users/{user_id}")
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    _admin: UserModel = Depends(require_admin),
):
    """Deactivate a user; admin-only."""
    user = crud.deactivate_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": f"User {user.username} deactivated"}
