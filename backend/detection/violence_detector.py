"""Temporal violence detector with a safe placeholder until weights exist."""

from collections import deque
from typing import List

import cv2
import numpy as np

from backend.config import settings
from backend.detection.base_detector import BaseDetector, Detection

CUSTOM_WEIGHTS = settings.MODELS_DIR / "violence.pt"
WINDOW_SIZE = 16
FRAME_RESIZE = (112, 112)


class ViolenceDetector(BaseDetector):
    def __init__(self, confidence_threshold: float = None):
        self.confidence_threshold = (
            confidence_threshold
            if confidence_threshold is not None
            else settings.CONFIDENCE_THRESHOLD
        )
        self.frame_buffer = deque(maxlen=WINDOW_SIZE)
        self.model = None
        self.using_custom_weights = False
        if CUSTOM_WEIGHTS.exists():
            self._load_model()
        else:
            print(f"[ViolenceDetector] Missing {CUSTOM_WEIGHTS}; placeholder mode.")

    def _load_model(self):
        # Replace with the architecture used to train violence.pt.
        # Keeping this hook isolated makes the temporal pipeline model-agnostic.
        self.using_custom_weights = True

    def detect(self, frame) -> List[Detection]:
        self.frame_buffer.append(cv2.resize(frame, FRAME_RESIZE))
        if not self.using_custom_weights or len(self.frame_buffer) < WINDOW_SIZE:
            return []

        clip = np.stack(self.frame_buffer, axis=0)
        confidence = 0.0  # TODO: run the trained action model on clip.
        if confidence < self.confidence_threshold:
            return []
        return [Detection("violence", confidence, None, "violence")]
