"""Persisted notification and alert-cooldown settings."""

from sqlalchemy import JSON, DateTime, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.config import settings as app_settings
from backend.database.database import Base

DEFAULT_COOLDOWN_BY_TYPE = {
    threat_type: app_settings.ALERT_COOLDOWN_SECONDS
    for threat_type in app_settings.THREAT_TYPES
}
DEFAULT_NOTIFY_BY_TYPE = {threat_type: True for threat_type in app_settings.THREAT_TYPES}


class SystemSettingsModel(Base):
    """Single-row application settings storage."""

    __tablename__ = "system_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    cooldown_by_type: Mapped[dict] = mapped_column(
        JSON, nullable=False, default=lambda: dict(DEFAULT_COOLDOWN_BY_TYPE)
    )
    notify_by_type: Mapped[dict] = mapped_column(
        JSON, nullable=False, default=lambda: dict(DEFAULT_NOTIFY_BY_TYPE)
    )
    updated_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def to_dict(self) -> dict:
        """Return the public settings representation."""

        return {
            "cooldown_by_type": self.cooldown_by_type,
            "notify_by_type": self.notify_by_type,
        }
