"""
Phase 1 entrypoint.

Goal of this file at this stage: prove that FastAPI, static file serving,
templates, and config loading all work together — BEFORE any video/AI
code is added. Run this, hit the endpoints below, and confirm everything
responds correctly. Later phases will add video streaming, detection,
DB, and Telegram routes on top of this skeleton.
"""
from fastapi import FastAPI, UploadFile, File, HTTPException
import threading
import time
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, Response, StreamingResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from backend.config import settings
from backend.database.database import init_db
from backend.database.db_listener import save_event_to_db
from backend.database.routes import router as events_router
from backend.detection.detector_manager import DetectorManager
from backend.events.event_manager import EventManager
from backend.utils.video_stream import VideoStream, WebcamManager
from backend.utils.upload_handler import (
    ALLOWED_IMAGE_EXTENSIONS,
    save_uploaded_file,
    list_uploaded_files,
)

app = FastAPI(
    title="AI-Driven Intelligent Surveillance System",
    description="Real-time threat detection with Telegram alerts",
    version="0.1.0",
)

# Serve screenshots, uploaded videos, and frontend static assets
app.mount("/static", StaticFiles(directory=str(settings.BASE_DIR / "static")), name="static")

templates = Jinja2Templates(directory=str(settings.BASE_DIR / "frontend" / "templates"))

_detector_manager = None
_detector_manager_lock = threading.Lock()
_event_manager = EventManager()


def get_detector_manager():
    """Load the expensive detection models once, on the first stream request."""
    global _detector_manager
    with _detector_manager_lock:
        if _detector_manager is None:
            _detector_manager = DetectorManager()
        return _detector_manager


def log_security_event(event):
    print(
        f"[EVENT] {event.event_type} ({event.confidence:.2f}) "
        f"from {event.source} -> {event.screenshot_path}"
    )


_event_manager.add_listener(log_security_event)
_event_manager.add_listener(save_event_to_db)


@app.on_event("startup")
def on_startup():
    """Initialize the database schema before serving requests."""
    init_db()


app.include_router(events_router)


def processed_mjpeg_frames(stream, source: str, target_fps: float = None):
    """Read, optionally analyze, annotate, and encode a video stream."""
    detector_manager = get_detector_manager()
    frame_interval = 1.0 / target_fps if target_fps else 0.0
    while True:
        success, frame, should_process = stream.read()
        if not success:
            break

        if should_process:
            try:
                detections = detector_manager.detect_all(frame)
                if detections:
                    _event_manager.process_detections(frame, detections, source=source)
                    frame = detector_manager.draw_all(frame, detections)
            except Exception as exc:
                # Detection failure must not terminate the video stream.
                print(f"[Detection] Failed to process {source}: {exc}")

        import cv2
        ok, buffer = cv2.imencode(".jpg", frame)
        if not ok:
            continue
        yield (
            b"--frame\r\nContent-Type: image/jpeg\r\n\r\n"
            + buffer.tobytes() + b"\r\n"
        )
        if frame_interval:
            time.sleep(frame_interval)


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Test dashboard: live webcam feed + upload-and-stream UI (Phase 2)."""
    return templates.TemplateResponse(request, "index.html", {})


@app.get("/health")
async def health_check():
    """Simple health check — used later for monitoring/deployment."""
    return {"status": "ok"}


@app.get("/config-check")
async def config_check():
    """
    Verifies .env values are being read correctly.
    Does NOT expose the actual bot token — only whether it's set.
    """
    return {
        "database_url": settings.DATABASE_URL,
        "confidence_threshold": settings.CONFIDENCE_THRESHOLD,
        "frame_skip": settings.FRAME_SKIP,
        "alert_cooldown_seconds": settings.ALERT_COOLDOWN_SECONDS,
        "threat_types": settings.THREAT_TYPES,
        "telegram_token_configured": bool(
            settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_BOT_TOKEN != "your_bot_token_here"
        ),
        "telegram_chat_id_configured": bool(
            settings.TELEGRAM_CHAT_ID and settings.TELEGRAM_CHAT_ID != "your_chat_id_here"
        ),
    }


@app.get("/video_feed")
async def video_feed():
    """
    Live webcam MJPEG stream. Embed with:
        <img src="/video_feed">
    Uses a shared webcam handle so multiple viewers don't each try to
    open the camera device separately.
    """
    try:
        stream = WebcamManager.get_stream(source=0)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=f"Webcam unavailable: {e}")

    def stream_frames():
        try:
            yield from processed_mjpeg_frames(stream, source="webcam")
        finally:
            # Closing/removing the <img> causes the request to disconnect.
            # Always release this client's camera lease in that case.
            WebcamManager.release_client(stream)

    return StreamingResponse(
        stream_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@app.post("/stop_webcam")
async def stop_webcam():
    """Immediately release the shared webcam device."""
    WebcamManager.release()
    _event_manager.debouncer.reset(source="webcam")
    return {"status": "stopped"}


@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    """
    Accepts a video or image upload and returns a stream URL for it.
    """
    filename = await save_uploaded_file(file)
    return {"filename": filename, "stream_url": f"/video_feed/uploaded/{filename}"}


@app.get("/uploads")
async def uploads_list():
    """Lists previously uploaded media available for analysis."""
    return {"files": list_uploaded_files()}


@app.get("/video_feed/uploaded/{filename}")
async def video_feed_uploaded(filename: str):
    """
    Streams a previously uploaded video file as MJPEG, throttled to a
    realistic playback rate (uploaded files would otherwise stream as
    fast as disk I/O allows, which is far faster than real-time).
    """
    filepath = settings.UPLOADS_DIR / filename

    # Prevent path traversal — only allow filenames actually inside UPLOADS_DIR
    if not filepath.resolve().is_relative_to(settings.UPLOADS_DIR.resolve()):
        raise HTTPException(status_code=400, detail="Invalid filename")
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Video not found")

    if filepath.suffix.lower() in ALLOWED_IMAGE_EXTENSIONS:
        import cv2

        frame = cv2.imread(str(filepath))
        if frame is None:
            raise HTTPException(status_code=400, detail="Could not read image")

        try:
            detections = get_detector_manager().detect_all(frame)
            if detections:
                _event_manager.process_detections(frame, detections, source=filename)
                frame = get_detector_manager().draw_all(frame, detections)
        except Exception as exc:
            print(f"[Detection] Failed to process image {filename}: {exc}")

        ok, buffer = cv2.imencode(".jpg", frame)
        if not ok:
            raise HTTPException(status_code=500, detail="Could not encode image")
        return Response(content=buffer.tobytes(), media_type="image/jpeg")

    try:
        stream = VideoStream(source=str(filepath))
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=f"Could not open video: {e}")

    def stream_frames():
        try:
            yield from processed_mjpeg_frames(stream, source=filename, target_fps=25)
        finally:
            stream.release()

    return StreamingResponse(
        stream_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.app:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG,
    )
