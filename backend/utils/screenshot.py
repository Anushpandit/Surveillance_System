"""Screenshot capture for confirmed security events."""

import uuid
from datetime import datetime

import cv2

from backend.config import settings


def save_screenshot(frame, event_type: str) -> str:
    """Save an event frame and return its filename."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{event_type}_{timestamp}_{uuid.uuid4().hex[:8]}.jpg"
    filepath = settings.SCREENSHOTS_DIR / filename
    if not cv2.imwrite(str(filepath), frame):
        raise IOError(f"Could not save screenshot: {filepath}")
    return filename
