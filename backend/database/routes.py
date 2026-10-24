"""Phase 5: API routes for event history, review, deletion, and analytics."""

import io
from urllib.parse import quote
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.database import crud
from backend.database.database import get_db
from backend.database.retention import cleanup_old_events, find_orphaned_screenshots
from backend.database.export import generate_csv, generate_pdf
from backend.auth.dependencies import get_current_user, require_admin
from backend.auth.models import UserModel

router = APIRouter(prefix="/api/events", tags=["events"])


def _event_response(event):
    """Serialize an event and expose its screenshot through the media mount."""

    payload = event.to_dict()
    if event.screenshot_path:
        payload["screenshot_url"] = "/media/screenshots/" + quote(
            event.screenshot_path, safe=""
        )
    else:
        payload["screenshot_url"] = None
    return payload


@router.get("/")
def list_events(
    event_type: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    min_confidence: float | None = Query(None, ge=0.0, le=1.0),
    max_confidence: float | None = Query(None, ge=0.0, le=1.0),
    reviewed: bool | None = None,
    source: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _user: UserModel = Depends(get_current_user),
):
    """Return filtered, paginated event history."""

    events = crud.get_events(
        db,
        event_type=event_type,
        start_date=start_date,
        end_date=end_date,
        min_confidence=min_confidence,
        max_confidence=max_confidence,
        reviewed=reviewed,
        source=source,
        skip=skip,
        limit=limit,
    )
    return {
        "total": crud.count_events(
            db,
            event_type=event_type,
            start_date=start_date,
            end_date=end_date,
            min_confidence=min_confidence,
            max_confidence=max_confidence,
            reviewed=reviewed,
            source=source,
        ),
        "skip": skip,
        "limit": limit,
        "events": [_event_response(event) for event in events],
    }


@router.get("/sources")
def list_sources(
    db: Session = Depends(get_db),
    _user: UserModel = Depends(get_current_user),
):
    """Return distinct event sources for the history filter."""

    return {"sources": crud.get_distinct_sources(db)}


@router.post("/maintenance/cleanup")
def cleanup_events(
    retention_days: int = Query(30, ge=1, le=3650),
    dry_run: bool = Query(True),
    db: Session = Depends(get_db),
    _admin: UserModel = Depends(require_admin),
):
    """Preview or perform admin-only event retention cleanup."""

    events_deleted, screenshots_deleted = cleanup_old_events(
        db, retention_days=retention_days, dry_run=dry_run
    )
    return {
        "dry_run": dry_run,
        "retention_days": retention_days,
        "events_deleted": events_deleted,
        "screenshots_deleted": screenshots_deleted,
    }


@router.get("/maintenance/orphaned-screenshots")
def orphaned_screenshots(
    db: Session = Depends(get_db),
    _admin: UserModel = Depends(require_admin),
):
    """List screenshot files not referenced by any event."""

    files = find_orphaned_screenshots(db)
    return {"files": files, "count": len(files)}


@router.get("/analytics/by-type")
def analytics_by_type(
    start_date: datetime | None = None,
    db: Session = Depends(get_db),
    _user: UserModel = Depends(get_current_user),
):
    """Return event counts grouped by threat type."""

    return crud.get_event_counts_by_type(db, start_date=start_date)


@router.get("/export")
def export_events(
    format: str = Query(..., pattern="^(csv|pdf)$"),
    event_type: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    db: Session = Depends(get_db),
    _user: UserModel = Depends(get_current_user),
):
    """Export filtered incident history as CSV or PDF."""

    events = crud.get_events(
        db,
        event_type=event_type,
        start_date=start_date,
        end_date=end_date,
        skip=0,
        limit=5000,
    )
    if not events:
        raise HTTPException(status_code=404, detail="No events match the given filters")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if format == "csv":
        content, media_type, filename = (
            generate_csv(events), "text/csv", f"incident_report_{timestamp}.csv"
        )
    else:
        content, media_type, filename = (
            generate_pdf(events, start_date, end_date),
            "application/pdf",
            f"incident_report_{timestamp}.pdf",
        )
    return StreamingResponse(
        io.BytesIO(content),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/{event_id}")
def get_event(
    event_id: int,
    db: Session = Depends(get_db),
    _user: UserModel = Depends(get_current_user),
):
    """Return one event by ID."""

    event = crud.get_event_by_id(db, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return _event_response(event)


@router.patch("/{event_id}/review")
def review_event(
    event_id: int,
    is_false_positive: bool = False,
    db: Session = Depends(get_db),
    _user: UserModel = Depends(get_current_user),
):
    """Mark an event as reviewed, optionally flagging it as false positive."""

    event = crud.mark_reviewed(db, event_id, is_false_positive=is_false_positive)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return _event_response(event)


@router.delete("/{event_id}")
def remove_event(
    event_id: int,
    db: Session = Depends(get_db),
    _admin: UserModel = Depends(require_admin),
):
    """Delete one event by ID."""

    if not crud.delete_event(db, event_id):
        raise HTTPException(status_code=404, detail="Event not found")
    return {"deleted": True, "event_id": event_id}
