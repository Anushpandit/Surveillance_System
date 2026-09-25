"""Confirmed security event, ready for persistence and notification."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Tuple


@dataclass
class SecurityEvent:
    event_type: str
    confidence: float
    timestamp: datetime
    source: str
    screenshot_path: str = ""
    label: str = ""
    bbox: Optional[Tuple[int, int, int, int]] = None

    def to_dict(self):
        return {
            "event_type": self.event_type,
            "confidence": round(self.confidence, 3),
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "screenshot_path": self.screenshot_path,
            "label": self.label,
        }
