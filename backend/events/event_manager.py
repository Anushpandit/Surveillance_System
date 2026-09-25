"""Detection -> debounce -> screenshot -> listener event pipeline."""

from datetime import datetime
from typing import Callable, List

from backend.detection.base_detector import Detection
from backend.events.debouncer import Debouncer
from backend.events.event import SecurityEvent
from backend.utils.screenshot import save_screenshot


class EventManager:
    def __init__(self, cooldown_seconds: int = None):
        self.debouncer = Debouncer(cooldown_seconds)
        self._listeners: List[Callable[[SecurityEvent], None]] = []

    def add_listener(self, callback: Callable[[SecurityEvent], None]):
        self._listeners.append(callback)

    def process_detections(self, frame, detections: List[Detection], source: str):
        confirmed_events = []
        for detection in detections:
            if not self.debouncer.should_fire(source, detection.event_type):
                continue

            annotated_frame = self._annotate_single(frame, detection)
            screenshot_filename = save_screenshot(annotated_frame, detection.event_type)
            event = SecurityEvent(
                event_type=detection.event_type,
                confidence=detection.confidence,
                timestamp=datetime.now(),
                source=source,
                screenshot_path=screenshot_filename,
                label=detection.label,
                bbox=detection.bbox,
            )
            confirmed_events.append(event)
            self._notify_listeners(event)
        return confirmed_events

    def _notify_listeners(self, event: SecurityEvent):
        for listener in self._listeners:
            try:
                listener(event)
            except Exception as exc:
                name = getattr(listener, "__name__", listener.__class__.__name__)
                print(f"[EventManager] Listener {name} failed: {exc}")

    @staticmethod
    def _annotate_single(frame, detection: Detection):
        import cv2

        annotated = frame.copy()
        if detection.bbox is None:
            return annotated
        x1, y1, x2, y2 = detection.bbox
        cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 0, 255), 2)
        cv2.putText(
            annotated, f"{detection.event_type} {detection.confidence:.2f}",
            (x1, max(y1 - 8, 12)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2,
        )
        return annotated
