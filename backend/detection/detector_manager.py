"""Orchestrates all configured detectors."""

from typing import List

from backend.detection.accident_detector import AccidentDetector
from backend.detection.base_detector import Detection
from backend.detection.fire_smoke_detector import FireSmokeDetector
from backend.detection.violence_detector import ViolenceDetector
from backend.detection.weapon_detector import WeaponDetector


class DetectorManager:
    def __init__(self):
        print("[DetectorManager] Loading detection models...")
        self.fire_smoke = FireSmokeDetector()
        self.weapon = WeaponDetector()
        self.violence = ViolenceDetector()
        self.accident = AccidentDetector()
        print("[DetectorManager] All detectors initialized.")

    def detect_all(self, frame) -> List[Detection]:
        detections = []
        detections.extend(self.fire_smoke.detect(frame))
        weapon_detections = self.weapon.detect(frame)
        detections.extend(self.violence.detect(frame))
        accident_detections = self.accident.detect(frame)

        # Do not let weak weapon-model false positives on cars hide a strong,
        # scene-level accident detection.  Conversely, for a localized
        # accident prediction, an overlapping weapon finding is more specific
        # and should win over the accident model's common armed-group error.
        frame_area = frame.shape[0] * frame.shape[1]
        strong_weapon = any(d.confidence >= 0.05 for d in weapon_detections)
        broad_accident = any(
            d.bbox is not None
            # Scene-level accident predictions commonly cover the damaged
            # vehicle and surrounding roadway, but not necessarily the full
            # frame.  This also prevents low-confidence weapon boxes on car
            # parts from masking a crash prediction.
            and self._box_area(d.bbox) >= frame_area * 0.25
            and d.confidence >= 0.55
            for d in accident_detections
        )
        if strong_weapon:
            # Clear weapon evidence is more specific than the accident
            # model's borderline scene-level false positive.
            detections.extend(weapon_detections)
        elif broad_accident:
            detections.extend(accident_detections)
        else:
            detections.extend(weapon_detections)
            detections.extend(
                d for d in accident_detections
                if not any(
                    d.bbox is not None and weapon.bbox is not None
                    and self._iou(d.bbox, weapon.bbox) > 0.1
                    for weapon in weapon_detections
                )
            )
        return detections

    @staticmethod
    def _box_area(box):
        return max(0, box[2] - box[0]) * max(0, box[3] - box[1])

    @staticmethod
    def _iou(box_a, box_b):
        xa1, ya1, xa2, ya2 = box_a
        xb1, yb1, xb2, yb2 = box_b
        intersection = max(0, min(xa2, xb2) - max(xa1, xb1)) * max(
            0, min(ya2, yb2) - max(ya1, yb1)
        )
        union = (
            DetectorManager._box_area(box_a)
            + DetectorManager._box_area(box_b)
            - intersection
        )
        return intersection / union if union else 0.0

    def draw_all(self, frame, detections: List[Detection]):
        return self.fire_smoke.draw_detections(frame, detections)
