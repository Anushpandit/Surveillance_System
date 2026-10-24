"""Single-frame weapon detection using a YOLO model."""

from typing import List

from ultralytics import YOLO

from backend.config import settings
from backend.detection.base_detector import BaseDetector, Detection

WEAPON_CLASSES = {"weapon", "gun", "pistol", "rifle", "knife"}


class WeaponDetector(BaseDetector):
    def __init__(self, confidence_threshold: float = None):
        self.confidence_threshold = (
            confidence_threshold
            if confidence_threshold is not None
            else settings.WEAPON_CONFIDENCE_THRESHOLD
        )
        self.using_custom_weights = settings.WEAPON_MODEL_PATH.exists()
        weights = (
            str(settings.WEAPON_MODEL_PATH)
            if self.using_custom_weights
            else "yolo11n.pt"
        )
        if not self.using_custom_weights:
            print(
                f"[WeaponDetector] Missing {settings.WEAPON_MODEL_PATH}; "
                "weapon detection disabled."
            )
        self.model = YOLO(weights)

    def detect(self, frame) -> List[Detection]:
        if not self.using_custom_weights:
            return []
        # Run overlapping crops as well as the full frame.  Weapons at the
        # edges of a group become very small when the whole image is resized
        # to the model's input size, while a crop gives them more pixels.
        height, width = frame.shape[:2]
        crop_width = max(int(width * 0.66), 1)
        starts = sorted({0, max(0, (width - crop_width) // 2), max(0, width - crop_width)})
        candidates = []

        for start in starts:
            end = min(width, start + crop_width)
            crop = frame[:, start:end]
            results = self.model(
                crop,
                conf=self.confidence_threshold,
                imgsz=640,
                verbose=False,
            )[0]
            for box in results.boxes:
                confidence = float(box.conf[0])
                class_id = int(box.cls[0])
                label = str(self.model.names[class_id]).lower()
                if confidence < self.confidence_threshold or label not in WEAPON_CLASSES:
                    continue
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                box_width = x2 - x1
                box_height = y2 - y1
                global_x1 = x1 + start
                # Very low thresholds expose large ground/watermark boxes.
                # Keep person/weapon-shaped candidates and discard those
                # tiny or unusually wide regions.
                if box_width < 12 or box_height < 24 or box_width >= box_height * 0.75:
                    continue
                # A low-confidence, near-edge box spanning much of the
                # image height is typically a pillar or other background
                # structure rather than a weapon carried by a person.
                if (
                    confidence < 0.005
                    and global_x1 >= width * 0.85
                    and box_height >= height * 0.45
                ):
                    continue
                candidates.append((
                    confidence,
                    (x1 + start, y1, x2 + start, y2),
                    label,
                ))

        # Keep the strongest prediction when overlapping crops identify the
        # same person/weapon.
        candidates.sort(key=lambda item: item[0], reverse=True)
        kept = []
        for candidate in candidates:
            if any(self._iou(candidate[1], previous[1]) > 0.25 for previous in kept):
                continue
            kept.append(candidate)

        return [Detection("weapon", confidence, bbox, label)
                for confidence, bbox, label in kept]

    @staticmethod
    def _iou(box_a, box_b):
        xa1, ya1, xa2, ya2 = box_a
        xb1, yb1, xb2, yb2 = box_b
        intersection = max(0, min(xa2, xb2) - max(xa1, xb1)) * max(
            0, min(ya2, yb2) - max(ya1, yb1)
        )
        area_a = max(0, xa2 - xa1) * max(0, ya2 - ya1)
        area_b = max(0, xb2 - xb1) * max(0, yb2 - yb1)
        union = area_a + area_b - intersection
        return intersection / union if union else 0.0
