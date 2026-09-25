"""Phase 5: Database engine and session management.

The engine is selected from ``DATABASE_URL`` in the centralized settings.
SQLite receives its thread-safety connection option automatically; other
database URLs, including PostgreSQL, use default connection arguments.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from backend.config import settings


connect_args = (
    {"check_same_thread": False}
    if settings.DATABASE_URL.startswith("sqlite")
    else {}
)

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class inherited by all SQLAlchemy ORM models."""


def get_db() -> Generator[Session, None, None]:
    """Yield a database session and close it after the request completes."""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create tables that do not yet exist.

    Alembic should be used for schema evolution once the initial schema is
    established; ``create_all`` intentionally does not alter existing tables.
    """

    from backend.database import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
