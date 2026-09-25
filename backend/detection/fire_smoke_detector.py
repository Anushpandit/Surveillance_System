"""Single-frame fire and smoke detection using a YOLO model."""

from typing import List

from ultralytics import YOLO

from backend.config import settings
from backend.detection.base_detector import BaseDetector, Detection

CUSTOM_WEIGHTS = settings.MODELS_DIR / "fire_smoke.pt"
FIRE_SMOKE_CLASSES = {"fire", "smoke"}


class FireSmokeDetector(BaseDetector):
    def __init__(self, confidence_threshold: float = None):
        self.confidence_threshold = (
            confidence_threshold
            if confidence_threshold is not None
            else settings.CONFIDENCE_THRESHOLD
        )
        self.using_custom_weights = CUSTOM_WEIGHTS.exists()
        weights = str(CUSTOM_WEIGHTS) if self.using_custom_weights else "yolo11n.pt"
        if not self.using_custom_weights:
            print(f"[FireSmokeDetector] Missing {CUSTOM_WEIGHTS}; using stock YOLO.")
        self.model = YOLO(weights)

    def detect(self, frame) -> List[Detection]:
        if not self.using_custom_weights:
            return []
        results = self.model(frame, verbose=False)[0]
        detections = []
        for box in results.boxes:
            confidence = float(box.conf[0])
            class_id = int(box.cls[0])
            label = str(self.model.names[class_id]).lower()
            if confidence < self.confidence_threshold or label not in FIRE_SMOKE_CLASSES:
                continue
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            detections.append(Detection(label, confidence, (x1, y1, x2, y2), label))
        return detections
