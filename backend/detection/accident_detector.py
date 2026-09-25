"""Accident detection using the trained accident classifier/detector."""

import math
from typing import Dict, List

from ultralytics import YOLO

from backend.config import settings
from backend.detection.base_detector import BaseDetector, Detection

VEHICLE_CLASSES = {"car", "truck", "bus", "motorcycle"}
VELOCITY_DROP_THRESHOLD = 25.0
OVERLAP_IOU_THRESHOLD = 0.3


class AccidentDetector(BaseDetector):
    def __init__(self, confidence_threshold: float = None):
        self.confidence_threshold = (
            confidence_threshold
            if confidence_threshold is not None
            else settings.CONFIDENCE_THRESHOLD
        )
        self.using_custom_weights = settings.ACCIDENT_MODEL_PATH.exists()
        weights = (
            str(settings.ACCIDENT_MODEL_PATH)
            if self.using_custom_weights
            else "yolo11n.pt"
        )
        if self.using_custom_weights:
            print(f"[AccidentDetector] Loading trained model: {settings.ACCIDENT_MODEL_PATH}")
        else:
            print(
                f"[AccidentDetector] Missing {settings.ACCIDENT_MODEL_PATH}; "
                "using vehicle-tracking fallback."
            )
        self.model = YOLO(weights)
        self.track_history: Dict[int, list] = {}

    def detect(self, frame) -> List[Detection]:
        if self.using_custom_weights:
            return self._detect_with_custom_model(frame)

        results = self.model.track(
            frame, persist=True, verbose=False,
            classes=self._vehicle_class_ids(),
        )[0]
        if results.boxes.id is None:
            return []

        boxes = results.boxes.xyxy.cpu().numpy()
        track_ids = results.boxes.id.cpu().numpy().astype(int)
        confidences = results.boxes.conf.cpu().numpy()
        current = {}
        for box, track_id, confidence in zip(boxes, track_ids, confidences):
            x1, y1, x2, y2 = box
            point = ((x1 + x2) / 2, (y1 + y2) / 2)
            bbox = (int(x1), int(y1), int(x2), int(y2))
            current[track_id] = (point[0], point[1], bbox, float(confidence))
            history = self.track_history.setdefault(track_id, [])
            history.append(point)
            if len(history) > 10:
                history.pop(0)

        detections = []
        for track_id, (_, _, bbox, confidence) in current.items():
            history = self.track_history[track_id]
            if len(history) >= 3:
                previous = self._velocity(history[-3], history[-2])
                current_velocity = self._velocity(history[-2], history[-1])
                if previous > VELOCITY_DROP_THRESHOLD and current_velocity < previous * 0.3:
                    detections.append(Detection(
                        "accident", min(0.9, confidence + 0.1), bbox, "sudden_stop",
                    ))

        ids = list(current)
        for index, first_id in enumerate(ids):
            for second_id in ids[index + 1:]:
                first_box, second_box = current[first_id][2], current[second_id][2]
                if self._iou(first_box, second_box) > OVERLAP_IOU_THRESHOLD:
                    detections.append(Detection(
                        "accident", 0.7, self._union_box(first_box, second_box),
                        "collision_overlap",
                    ))
        return [d for d in detections if d.confidence >= self.confidence_threshold]

    def _detect_with_custom_model(self, frame) -> List[Detection]:
        """Run the trained model and emit only its Accident class."""
        results = self.model(frame, verbose=False)[0]
        detections = []
        for box in results.boxes:
            confidence = float(box.conf[0])
            if confidence < self.confidence_threshold:
                continue

            class_id = int(box.cls[0])
            label = str(self.model.names[class_id]).strip().lower()
            if label not in {"accident", "crash", "collision"}:
                continue

            x1, y1, x2, y2 = map(int, box.xyxy[0])
            detections.append(
                Detection(
                    "accident",
                    confidence,
                    (x1, y1, x2, y2),
                    label,
                )
            )
        return detections

    def _vehicle_class_ids(self):
        return [key for key, value in self.model.names.items() if value in VEHICLE_CLASSES]

    @staticmethod
    def _velocity(first, second):
        return math.hypot(second[0] - first[0], second[1] - first[1])

    @staticmethod
    def _iou(box_a, box_b):
        xa1, ya1, xa2, ya2 = box_a
        xb1, yb1, xb2, yb2 = box_b
        intersection = max(0, min(xa2, xb2) - max(xa1, xb1)) * max(0, min(ya2, yb2) - max(ya1, yb1))
        area_a = max(0, xa2 - xa1) * max(0, ya2 - ya1)
        area_b = max(0, xb2 - xb1) * max(0, yb2 - yb1)
        union = area_a + area_b - intersection
        return intersection / union if union else 0.0

    @staticmethod
    def _union_box(box_a, box_b):
        return (
            min(box_a[0], box_b[0]), min(box_a[1], box_b[1]),
            max(box_a[2], box_b[2]), max(box_a[3], box_b[3]),
        )
