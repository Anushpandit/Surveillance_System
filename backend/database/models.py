"""Phase 5: SQLAlchemy ORM models for persisted security events."""

from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.database import Base


class EventModel(Base):
    """Database representation of an in-memory ``SecurityEvent``."""

    __tablename__ = "events"
    __table_args__ = (
        Index("ix_events_type_timestamp", "event_type", "timestamp"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    screenshot_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reviewed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_false_positive: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation for API responses."""

        return {
            "id": self.id,
            "event_type": self.event_type,
            "label": self.label,
            "confidence": round(self.confidence, 3),
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "source": self.source,
            "screenshot_path": self.screenshot_path,
            "reviewed": self.reviewed,
            "is_false_positive": self.is_false_positive,
        }
