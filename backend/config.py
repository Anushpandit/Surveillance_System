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
    # --- Telegram ---
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")

    # --- Database ---
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./surveillance.db")

    # --- Detection ---
    CONFIDENCE_THRESHOLD: float = float(os.getenv("CONFIDENCE_THRESHOLD", 0.6))
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
                / "Accident_detect_dataset"
                / "runs"
                / "detect"
                / "training_runs"
                / "yolo_100_epochs"
                / "weights"
                / "best.pt"
            ),
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
