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
        detections.extend(self.weapon.detect(frame))
        detections.extend(self.violence.detect(frame))
        detections.extend(self.accident.detect(frame))
        return detections

    def draw_all(self, frame, detections: List[Detection]):
        return self.fire_smoke.draw_detections(frame, detections)
