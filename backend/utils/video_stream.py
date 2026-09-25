"""
Phase 2: Video ingestion.

VideoStream wraps cv2.VideoCapture for both live webcam feeds and
uploaded video files behind one common interface. It also handles
frame skipping so that later (in Phase 3) we don't run expensive
AI inference on every single frame.

Design note: this class only handles CAPTURE + ENCODING for streaming
to the browser. Detection logic is intentionally NOT here — Phase 3
will hook into `frames()` to run models on sampled frames without
touching this module.
"""
import cv2
import time
import threading
from typing import Optional, Union

from backend.config import settings


class VideoStream:
    """
    Wraps a video source (webcam index or file path) and exposes:
      - frames(): generator yielding raw BGR numpy frames (every frame)
      - mjpeg_frames(): generator yielding JPEG-encoded bytes for HTTP streaming
      - frame_skip: only every Nth frame is marked "for processing" via
        should_process flag, so Phase 3 detection can subsample cheaply.
    """

    def __init__(self, source: Union[int, str] = 0, frame_skip: Optional[int] = None):
        """
        source: 0 (or another int) for a webcam index, or a file path
                (str) for an uploaded video.
        frame_skip: process every Nth frame for AI (doesn't affect the
                    raw display stream, only the `should_process` flag).
        """
        self.source = source
        self.frame_skip = frame_skip if frame_skip is not None else settings.FRAME_SKIP
        self._frame_count = 0
        self._lock = threading.Lock()
        self._cap = cv2.VideoCapture(source)

        if not self._cap.isOpened():
            raise RuntimeError(f"Could not open video source: {source}")

    def is_opened(self) -> bool:
        return self._cap.isOpened()

    def read(self):
        """
        Reads a single frame.
        Returns (success, frame, should_process).
        should_process is True only every `frame_skip`-th frame —
        Phase 3 will use this to decide whether to run detection.
        """
        with self._lock:
            success, frame = self._cap.read()
            if not success:
                return False, None, False

            self._frame_count += 1
            should_process = (self._frame_count % self.frame_skip == 0)
            return True, frame, should_process

    def frames(self):
        """Generator yielding (frame, should_process) tuples until the source ends."""
        while True:
            success, frame, should_process = self.read()
            if not success:
                break
            yield frame, should_process

    def mjpeg_frames(self, target_fps: Optional[float] = None):
        """
        Generator yielding JPEG-encoded frame bytes formatted as
        multipart HTTP chunks, ready for a StreamingResponse with
        media type 'multipart/x-mixed-replace; boundary=frame'.

        target_fps: if set, throttles output to roughly this rate.
        Useful for uploaded files, which would otherwise stream as
        fast as the disk can read (way faster than real playback speed).
        """
        frame_interval = (1.0 / target_fps) if target_fps else 0
        while True:
            success, frame, _ = self.read()
            if not success:
                break

            ok, buffer = cv2.imencode(".jpg", frame)
            if not ok:
                continue

            chunk = (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"
            )
            yield chunk

            if frame_interval:
                time.sleep(frame_interval)

    def release(self):
        with self._lock:
            self._cap.release()

    def __del__(self):
        try:
            self.release()
        except Exception:
            pass


class WebcamManager:
    """
    Manages a single shared webcam VideoStream so multiple dashboard
    clients viewing the live feed don't each open a separate camera
    handle (which would fail on most hardware).
    """
    _instance: Optional[VideoStream] = None
    _lock = threading.Lock()
    _clients = 0

    @classmethod
    def get_stream(cls, source: Union[int, str] = 0) -> VideoStream:
        with cls._lock:
            if cls._instance is None or not cls._instance.is_opened():
                cls._instance = VideoStream(source=source)
                cls._clients = 0
            cls._clients += 1
            return cls._instance

    @classmethod
    def release_client(cls, stream: Optional[VideoStream] = None):
        """Release one HTTP client and close the camera when none remain."""
        with cls._lock:
            if cls._instance is None or (stream is not None and stream is not cls._instance):
                return

            cls._clients = max(0, cls._clients - 1)
            if cls._clients == 0:
                cls._instance.release()
                cls._instance = None

    @classmethod
    def release(cls):
        """Force-release the shared webcam, for application shutdown."""
        with cls._lock:
            if cls._instance is not None:
                cls._instance.release()
                cls._instance = None
            cls._clients = 0
