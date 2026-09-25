"""Bridge the Phase 4 event pipeline to database persistence."""

import logging

from backend.database.crud import create_event
from backend.database.database import SessionLocal
from backend.events.event import SecurityEvent

logger = logging.getLogger(__name__)


def save_event_to_db(event: SecurityEvent) -> None:
    """Persist one event using a short-lived, listener-owned session."""

    db = SessionLocal()
    try:
        create_event(db, event)
    except Exception:
        logger.exception("Failed to persist security event %s", event.event_type)
        raise
    finally:
        db.close()
