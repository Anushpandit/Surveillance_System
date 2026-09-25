"""Phase 5: Centralized CRUD operations for security events."""

from datetime import datetime

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from backend.database.models import EventModel
from backend.events.event import SecurityEvent


def create_event(db: Session, event: SecurityEvent) -> EventModel:
    """Persist a ``SecurityEvent`` and return the refreshed database row."""

    db_event = EventModel(
        event_type=event.event_type,
        label=event.label,
        confidence=event.confidence,
        timestamp=event.timestamp,
        source=event.source,
        screenshot_path=event.screenshot_path,
        reviewed=False,
        is_false_positive=False,
    )
    try:
        db.add(db_event)
        db.commit()
        db.refresh(db_event)
    except Exception:
        db.rollback()
        raise
    return db_event


def get_event_by_id(db: Session, event_id: int) -> EventModel | None:
    """Return one event by ID, or ``None`` when it does not exist."""

    return db.query(EventModel).filter(EventModel.id == event_id).first()


def get_events(
    db: Session,
    event_type: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    min_confidence: float | None = None,
    reviewed: bool | None = None,
    source: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[EventModel]:
    """Return newest-first events matching all supplied filters."""

    query = db.query(EventModel)
    if event_type is not None:
        query = query.filter(EventModel.event_type == event_type)
    if start_date is not None:
        query = query.filter(EventModel.timestamp >= start_date)
    if end_date is not None:
        query = query.filter(EventModel.timestamp <= end_date)
    if min_confidence is not None:
        query = query.filter(EventModel.confidence >= min_confidence)
    if reviewed is not None:
        query = query.filter(EventModel.reviewed == reviewed)
    if source is not None:
        query = query.filter(EventModel.source == source)

    return query.order_by(desc(EventModel.timestamp)).offset(skip).limit(limit).all()


def count_events(db: Session, event_type: str | None = None) -> int:
    """Count persisted events, optionally restricted to one event type."""

    query = db.query(EventModel)
    if event_type is not None:
        query = query.filter(EventModel.event_type == event_type)
    return query.count()


def mark_reviewed(
    db: Session,
    event_id: int,
    is_false_positive: bool = False,
) -> EventModel | None:
    """Mark an event as reviewed and optionally as a false positive."""

    db_event = get_event_by_id(db, event_id)
    if db_event is None:
        return None
    db_event.reviewed = True
    db_event.is_false_positive = is_false_positive
    try:
        db.commit()
        db.refresh(db_event)
    except Exception:
        db.rollback()
        raise
    return db_event


def delete_event(db: Session, event_id: int) -> bool:
    """Delete an event record and return whether a row was deleted."""

    db_event = get_event_by_id(db, event_id)
    if db_event is None:
        return False
    try:
        db.delete(db_event)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return True


def get_event_counts_by_type(
    db: Session,
    start_date: datetime | None = None,
) -> dict[str, int]:
    """Return event counts grouped by event type for dashboard analytics."""

    query = db.query(EventModel.event_type, func.count(EventModel.id))
    if start_date is not None:
        query = query.filter(EventModel.timestamp >= start_date)
    results = query.group_by(EventModel.event_type).all()
    return {event_type: count for event_type, count in results}
