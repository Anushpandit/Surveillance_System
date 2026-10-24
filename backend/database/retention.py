"""Manual data-retention and orphaned-screenshot maintenance utilities."""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from backend.config import settings
from backend.database.models import EventModel

logger = logging.getLogger(__name__)


def _screenshot_file(path: str):
    """Resolve a stored screenshot filename safely inside the screenshot dir."""

    candidate = (settings.SCREENSHOTS_DIR / path).resolve()
    if not candidate.is_relative_to(settings.SCREENSHOTS_DIR.resolve()):
        return None
    return candidate


def cleanup_old_events(
    db: Session,
    retention_days: int,
    dry_run: bool = False,
) -> tuple[int, int]:
    """Delete events and screenshots older than a retention window.

    Returns ``(events_deleted, screenshots_deleted)``. In dry-run mode these
    counts describe what would be removed without changing the database/files.
    """

    if retention_days < 1:
        raise ValueError("retention_days must be at least 1")
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    old_events = db.query(EventModel).filter(
        EventModel.timestamp < cutoff.replace(tzinfo=None)
    ).all()
    events_deleted = 0
    screenshots_deleted = 0

    for event in old_events:
        screenshot = _screenshot_file(event.screenshot_path) if event.screenshot_path else None
        if screenshot is not None and screenshot.exists():
            screenshots_deleted += 1
            if not dry_run:
                try:
                    screenshot.unlink()
                except OSError as exc:
                    logger.warning("Could not delete screenshot %s: %s", screenshot, exc)
                    screenshots_deleted -= 1
        events_deleted += 1
        if not dry_run:
            db.delete(event)

    if not dry_run:
        db.commit()
    logger.info(
        "[Retention] %s %d events and %d screenshots (retention: %d days)",
        "Would delete" if dry_run else "Deleted",
        events_deleted,
        screenshots_deleted,
        retention_days,
    )
    return events_deleted, screenshots_deleted


def find_orphaned_screenshots(db: Session) -> list[str]:
    """Return screenshot files on disk that have no corresponding event."""

    if not settings.SCREENSHOTS_DIR.exists():
        return []
    referenced = {
        row[0] for row in db.query(EventModel.screenshot_path).all() if row[0]
    }
    return sorted(
        str(path)
        for path in settings.SCREENSHOTS_DIR.iterdir()
        if path.is_file() and path.name not in referenced
    )
