"""
Centralized configuration for the surveillance system.
All other modules should import settings from here instead of
reading os.environ directly, so config stays in one place.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Settings:
    # --- Authentication ---
    JWT_SECRET_KEY: str = os.getenv(
        "JWT_SECRET_KEY", "CHANGE_ME_IN_PRODUCTION_dev_only_secret"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24)
    )
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("PASSWORD_RESET_TOKEN_EXPIRE_MINUTES", 30)
    )

    # --- Telegram ---
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")

    # --- Database ---
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./surveillance.db")

    # --- Detection ---
    CONFIDENCE_THRESHOLD: float = float(os.getenv("CONFIDENCE_THRESHOLD", 0.6))
    # The weapon model is trained as a single-class detector.  Its current
    # weights produce useful detections below 0.01 confidence, so using the
    # generic 0.25 cutoff would silently hide weapons.
    WEAPON_CONFIDENCE_THRESHOLD: float = float(
        os.getenv("WEAPON_CONFIDENCE_THRESHOLD", 0.0015)
    )
    # The accident model is trained on a harder, scene-level dataset and
    # commonly produces useful detections just below the global threshold.
    ACCIDENT_CONFIDENCE_THRESHOLD: float = float(
        os.getenv("ACCIDENT_CONFIDENCE_THRESHOLD", 0.5)
    )
    FRAME_SKIP: int = int(os.getenv("FRAME_SKIP", 5))
    ALERT_COOLDOWN_SECONDS: int = int(os.getenv("ALERT_COOLDOWN_SECONDS", 45))

    # --- Trained detection models ---
    # Keep the accident model configurable so deployments can provide a
    # different weights file without changing application code.
    ACCIDENT_MODEL_PATH: Path = Path(
        os.getenv(
            "ACCIDENT_MODEL_PATH",
            str(
                BASE_DIR
                / "data"
                / "Accident_detect"
                / "best.pt"
            ),
        )
    ).expanduser()

    # The weapon dataset is a single-class YOLO detector (`weapon`).
    # Keep the path configurable so deployments can provide refreshed weights.
    WEAPON_MODEL_PATH: Path = Path(
        os.getenv(
            "WEAPON_MODEL_PATH",
            str(BASE_DIR / "data" / "Weapon_detect" / "best.pt"),
        )
    ).expanduser()

    # --- App ---
    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT: int = int(os.getenv("APP_PORT", 8000))
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"

    # --- Paths ---
    BASE_DIR: Path = BASE_DIR
    MODELS_DIR: Path = BASE_DIR / "backend" / "models"
    SCREENSHOTS_DIR: Path = BASE_DIR / "static" / "screenshots"
    UPLOADS_DIR: Path = BASE_DIR / "static" / "uploads"

    # Threat types the system recognizes (used across detection, DB, dashboard)
    THREAT_TYPES = ["fire", "smoke", "weapon", "violence", "accident"]


settings = Settings()

# Ensure required directories exist at startup
settings.SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
settings.UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
settings.MODELS_DIR.mkdir(parents=True, exist_ok=True)
