"""Shared detector interface and detection result type."""

from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass
class Detection:
    event_type: str
    confidence: float
    bbox: Optional[Tuple[int, int, int, int]] = None
    label: str = ""


class BaseDetector:
    """Interface implemented by every detector."""

    def detect(self, frame) -> List[Detection]:
        raise NotImplementedError

    def draw_detections(self, frame, detections: List[Detection]):
        import cv2

        annotated = frame.copy()
        for detection in detections:
            if detection.bbox is None:
                continue
            x1, y1, x2, y2 = detection.bbox
            color = self._color_for(detection.event_type)
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            text = f"{detection.event_type} {detection.confidence:.2f}"
            cv2.putText(
                annotated, text, (x1, max(y1 - 8, 12)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2,
            )
        return annotated

    @staticmethod
    def _color_for(event_type: str):
        return {
            "fire": (0, 69, 255),
            "smoke": (128, 128, 128),
            "weapon": (0, 0, 255),
            "violence": (0, 0, 200),
            "accident": (0, 165, 255),
        }.get(event_type, (255, 255, 255))
