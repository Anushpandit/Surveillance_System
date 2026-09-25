"""Connect Phase 3 detectors to the Phase 4 event pipeline."""

from backend.detection.detector_manager import DetectorManager
from backend.events.event_manager import EventManager
from backend.utils.video_stream import VideoStream


def run_surveillance(source, source_label: str):
    manager = DetectorManager()
    event_manager = EventManager()

    def log_to_console(event):
        print(
            f"[EVENT] {event.event_type} ({event.confidence:.2f}) "
            f"from {event.source} @ {event.timestamp} -> {event.screenshot_path}"
        )

    event_manager.add_listener(log_to_console)
    stream = VideoStream(source=source)
    try:
        for frame, should_process in stream.frames():
            if not should_process:
                continue
            detections = manager.detect_all(frame)
            if detections:
                event_manager.process_detections(frame, detections, source_label)
    finally:
        stream.release()
