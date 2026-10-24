"""Authenticated system-settings API routes."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_current_user, require_admin
from backend.auth.models import UserModel
from backend.config import settings as app_settings
from backend.database import system_settings_crud
from backend.database.database import get_db

router = APIRouter(prefix="/api/settings", tags=["settings"])


class SettingsUpdate(BaseModel):
    """Partial settings update payload."""

    cooldown_by_type: dict[str, int] | None = None
    notify_by_type: dict[str, bool] | None = None


def _validate(payload: SettingsUpdate) -> None:
    """Validate threat keys and cooldown values before persistence."""

    allowed = set(app_settings.THREAT_TYPES)
    for values in (payload.cooldown_by_type, payload.notify_by_type):
        if values and not set(values).issubset(allowed):
            raise HTTPException(status_code=400, detail="Unknown threat type in settings")
    if payload.cooldown_by_type and any(
        value < 0 or value > 86400 for value in payload.cooldown_by_type.values()
    ):
        raise HTTPException(status_code=400, detail="Cooldowns must be between 0 and 86400 seconds")


@router.get("/")
def read_settings(
    db: Session = Depends(get_db),
    _user: UserModel = Depends(get_current_user),
):
    """Return current settings to authenticated dashboard users."""

    return system_settings_crud.get_settings(db).to_dict()


@router.patch("/")
def update_settings(
    payload: SettingsUpdate,
    db: Session = Depends(get_db),
    _admin: UserModel = Depends(require_admin),
):
    """Update cooldowns and notification preferences for administrators."""

    _validate(payload)
    return system_settings_crud.update_settings(
        db, payload.cooldown_by_type, payload.notify_by_type
    ).to_dict()
