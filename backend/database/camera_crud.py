"""Database operations for configured cameras."""

from sqlalchemy.orm import Session

from backend.database.camera_model import CameraModel


def list_cameras(db: Session) -> list[CameraModel]:
    """Return cameras in creation order."""

    return db.query(CameraModel).order_by(CameraModel.id).all()


def get_camera(db: Session, camera_id: int) -> CameraModel | None:
    """Return one camera by ID."""

    return db.query(CameraModel).filter(CameraModel.id == camera_id).first()


def create_camera(db: Session, name: str, source: str) -> CameraModel:
    """Create an active camera."""

    camera = CameraModel(name=name.strip(), source=source.strip(), active=True)
    db.add(camera)
    db.commit()
    db.refresh(camera)
    return camera


def set_camera_active(db: Session, camera: CameraModel, active: bool) -> CameraModel:
    """Set camera active state and persist it."""

    camera.active = active
    db.commit()
    db.refresh(camera)
    return camera


def delete_camera(db: Session, camera: CameraModel) -> None:
    """Delete a camera row."""

    db.delete(camera)
    db.commit()
