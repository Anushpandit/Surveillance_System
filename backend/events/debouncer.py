"""Thread-safe cooldown tracking for confirmed events."""

import threading
import time
from typing import Dict, Optional, Tuple

from backend.config import settings


class Debouncer:
    def __init__(self, cooldown_seconds: Optional[int] = None):
        self.cooldown_seconds = (
            cooldown_seconds
            if cooldown_seconds is not None
            else settings.ALERT_COOLDOWN_SECONDS
        )
        self._last_fired: Dict[Tuple[str, str], float] = {}
        self._lock = threading.Lock()

    def should_fire(self, source: str, event_type: str) -> bool:
        key = (source, event_type)
        now = time.time()
        with self._lock:
            last_time = self._last_fired.get(key, 0.0)
            if now - last_time < self.cooldown_seconds:
                return False
            self._last_fired[key] = now
            return True

    def time_until_next_allowed(self, source: str, event_type: str) -> float:
        with self._lock:
            last_time = self._last_fired.get((source, event_type), 0.0)
            return max(0.0, self.cooldown_seconds - (time.time() - last_time))

    def reset(self, source: Optional[str] = None, event_type: Optional[str] = None):
        with self._lock:
            if source is None and event_type is None:
                self._last_fired.clear()
                return
            keys = [
                key for key in self._last_fired
                if (source is None or key[0] == source)
                and (event_type is None or key[1] == event_type)
            ]
            for key in keys:
                del self._last_fired[key]
