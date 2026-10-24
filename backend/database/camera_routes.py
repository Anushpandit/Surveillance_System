"""Authenticated multi-camera configuration and feed routes."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_current_user, require_admin
from backend.auth.models import UserModel
from backend.database import camera_crud
from backend.database.database import get_db
from backend.utils.video_stream import CameraStreamManager, resolve_source

router = APIRouter(prefix="/api/cameras", tags=["cameras"])


class CameraCreate(BaseModel):
    """Camera creation payload."""

    name: str = Field(min_length=1, max_length=100)
    source: str = Field(min_length=1, max_length=500)


@router.get("/")
def list_cameras(
    db: Session = Depends(get_db),
    _user: UserModel = Depends(get_current_user),
):
    """List configured cameras."""

    return {"cameras": [camera.to_dict() for camera in camera_crud.list_cameras(db)]}


@router.post("/", status_code=201)
def create_camera(
    payload: CameraCreate,
    db: Session = Depends(get_db),
    _admin: UserModel = Depends(require_admin),
):
    """Create a camera; administrators only."""

    return camera_crud.create_camera(db, payload.name, payload.source).to_dict()


@router.patch("/{camera_id}/active")
def set_active(
    camera_id: int,
    active: bool,
    db: Session = Depends(get_db),
    _admin: UserModel = Depends(require_admin),
):
    """Enable or disable a camera and immediately release disabled streams."""

    camera = camera_crud.get_camera(db, camera_id)
    if camera is None:
        raise HTTPException(status_code=404, detail="Camera not found")
    updated = camera_crud.set_camera_active(db, camera, active)
    if not active:
        CameraStreamManager.release(camera_id)
    return updated.to_dict()


@router.delete("/{camera_id}")
def remove_camera(
    camera_id: int,
    db: Session = Depends(get_db),
    _admin: UserModel = Depends(require_admin),
):
    """Delete a camera and release its stream."""

    camera = camera_crud.get_camera(db, camera_id)
    if camera is None:
        raise HTTPException(status_code=404, detail="Camera not found")
    CameraStreamManager.release(camera_id)
    camera_crud.delete_camera(db, camera)
    return {"deleted": True, "camera_id": camera_id}


@router.get("/{camera_id}/feed")
def camera_feed(
    camera_id: int,
    db: Session = Depends(get_db),
    _user: UserModel = Depends(get_current_user),
):
    """Stream an active configured camera as MJPEG."""

    camera = camera_crud.get_camera(db, camera_id)
    if camera is None:
        raise HTTPException(status_code=404, detail="Camera not found")
    if not camera.active:
        raise HTTPException(status_code=409, detail="Camera is inactive")
    try:
        stream = CameraStreamManager.get_stream(camera_id, resolve_source(camera.source))
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=503, detail=f"Camera unavailable: {exc}") from exc

    def frames():
        try:
            yield from stream.mjpeg_frames(target_fps=25)
        finally:
            CameraStreamManager.release_client(camera_id, stream)

    return StreamingResponse(frames(), media_type="multipart/x-mixed-replace; boundary=frame")
