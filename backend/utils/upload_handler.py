"""Validate and save uploaded media files."""
import uuid
from pathlib import Path

from fastapi import UploadFile, HTTPException

from backend.config import settings

ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
ALLOWED_EXTENSIONS = ALLOWED_VIDEO_EXTENSIONS | ALLOWED_IMAGE_EXTENSIONS
MAX_FILE_SIZE_MB = 500


async def save_uploaded_file(file: UploadFile) -> str:
    """
    Validates and saves an uploaded video or image to static/uploads/.
    Returns the saved filename (not full path).
    Raises HTTPException on invalid file type or size.
    """
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {sorted(ALLOWED_EXTENSIONS)}",
        )

    # Generate a unique filename to avoid collisions/overwrites
    safe_filename = f"{uuid.uuid4().hex}{ext}"
    destination = settings.UPLOADS_DIR / safe_filename

    size_bytes = 0
    max_bytes = MAX_FILE_SIZE_MB * 1024 * 1024

    with open(destination, "wb") as out_file:
        while chunk := await file.read(1024 * 1024):  # read in 1MB chunks
            size_bytes += len(chunk)
            if size_bytes > max_bytes:
                out_file.close()
                destination.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=400,
                    detail=f"File too large. Max size is {MAX_FILE_SIZE_MB}MB.",
                )
            out_file.write(chunk)

    return safe_filename


def list_uploaded_files() -> list[str]:
    """Return supported uploaded video and image filenames."""
    if not settings.UPLOADS_DIR.exists():
        return []
    return sorted(
        f.name for f in settings.UPLOADS_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in ALLOWED_EXTENSIONS
    )


# Backwards-compatible aliases for callers using the original video names.
save_uploaded_video = save_uploaded_file
list_uploaded_videos = list_uploaded_files
