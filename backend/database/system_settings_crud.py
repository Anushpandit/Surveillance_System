"""CRUD helpers for persisted system settings."""

from sqlalchemy.orm import Session

from backend.config import settings as app_settings
from backend.database.system_settings_model import (
    DEFAULT_COOLDOWN_BY_TYPE,
    DEFAULT_NOTIFY_BY_TYPE,
    SystemSettingsModel,
)


def get_settings(db: Session) -> SystemSettingsModel:
    """Get or initialize the single settings row."""

    row = db.query(SystemSettingsModel).filter(SystemSettingsModel.id == 1).first()
    if row is None:
        row = SystemSettingsModel(
            id=1,
            cooldown_by_type=dict(DEFAULT_COOLDOWN_BY_TYPE),
            notify_by_type=dict(DEFAULT_NOTIFY_BY_TYPE),
        )
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def update_settings(
    db: Session,
    cooldown_by_type: dict | None = None,
    notify_by_type: dict | None = None,
) -> SystemSettingsModel:
    """Merge and persist supplied settings fields."""

    row = get_settings(db)
    if cooldown_by_type is not None:
        values = dict(row.cooldown_by_type or {})
        values.update(cooldown_by_type)
        row.cooldown_by_type = values
    if notify_by_type is not None:
        values = dict(row.notify_by_type or {})
        values.update(notify_by_type)
        row.notify_by_type = values
    db.commit()
    db.refresh(row)
    return row


def get_cooldown_for_type(db: Session, event_type: str) -> int:
    """Return the configured cooldown for one threat type."""

    row = get_settings(db)
    return int((row.cooldown_by_type or {}).get(event_type, app_settings.ALERT_COOLDOWN_SECONDS))


def is_notification_enabled(db: Session, event_type: str) -> bool:
    """Return whether Telegram notifications are enabled for a threat type."""

    row = get_settings(db)
    return bool((row.notify_by_type or {}).get(event_type, True))
