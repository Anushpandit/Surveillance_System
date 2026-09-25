"""Phase 5: API routes for event history, review, deletion, and analytics."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database import crud
from backend.database.database import get_db

router = APIRouter(prefix="/api/events", tags=["events"])


@router.get("/")
def list_events(
    event_type: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    min_confidence: float | None = Query(None, ge=0.0, le=1.0),
    reviewed: bool | None = None,
    source: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Return filtered, paginated event history."""

    events = crud.get_events(
        db,
        event_type=event_type,
        start_date=start_date,
        end_date=end_date,
        min_confidence=min_confidence,
        reviewed=reviewed,
        source=source,
        skip=skip,
        limit=limit,
    )
    return {
        "total": crud.count_events(db, event_type=event_type),
        "skip": skip,
        "limit": limit,
        "events": [event.to_dict() for event in events],
    }


@router.get("/analytics/by-type")
def analytics_by_type(
    start_date: datetime | None = None,
    db: Session = Depends(get_db),
):
    """Return event counts grouped by threat type."""

    return crud.get_event_counts_by_type(db, start_date=start_date)


@router.get("/{event_id}")
def get_event(event_id: int, db: Session = Depends(get_db)):
    """Return one event by ID."""

    event = crud.get_event_by_id(db, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return event.to_dict()


@router.patch("/{event_id}/review")
def review_event(
    event_id: int,
    is_false_positive: bool = False,
    db: Session = Depends(get_db),
):
    """Mark an event as reviewed, optionally flagging it as false positive."""

    event = crud.mark_reviewed(db, event_id, is_false_positive=is_false_positive)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return event.to_dict()


@router.delete("/{event_id}")
def remove_event(event_id: int, db: Session = Depends(get_db)):
    """Delete one event by ID."""

    if not crud.delete_event(db, event_id):
        raise HTTPException(status_code=404, detail="Event not found")
    return {"deleted": True, "event_id": event_id}
