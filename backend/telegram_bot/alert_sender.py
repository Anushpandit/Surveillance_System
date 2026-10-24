"""Synchronous Telegram alert delivery for confirmed security events."""

import logging
import time
from pathlib import Path

import requests

from backend.config import settings
from backend.events.event import SecurityEvent

logger = logging.getLogger(__name__)

TELEGRAM_API_BASE = "https://api.telegram.org"
REQUEST_TIMEOUT_SECONDS = 10
MAX_RETRIES = 2
RETRY_DELAY_SECONDS = 2

EVENT_EMOJI = {
    "fire": "🔥",
    "smoke": "💨",
    "weapon": "🔫",
    "violence": "⚠️",
    "accident": "🚗",
}


class TelegramConfigError(Exception):
    """Raised when Telegram configuration is missing or invalid."""


def _build_caption(event: SecurityEvent) -> str:
    emoji = EVENT_EMOJI.get(event.event_type, "🚨")
    label_line = f"\nDetail: {event.label}" if event.label else ""
    return (
        f"{emoji} *THREAT DETECTED: {event.event_type.upper()}*\n"
        f"Confidence: {event.confidence:.0%}\n"
        f"Time: {event.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"Source: {event.source}"
        f"{label_line}"
    )


def _is_configured() -> bool:
    return bool(
        settings.TELEGRAM_BOT_TOKEN
        and settings.TELEGRAM_BOT_TOKEN != "your_bot_token_here"
        and settings.TELEGRAM_CHAT_ID
        and settings.TELEGRAM_CHAT_ID != "your_chat_id_here"
    )


def _is_notification_enabled_for(event_type: str) -> bool:
    """Read the per-threat Telegram preference with an enabled fallback."""

    try:
        from backend.database.database import SessionLocal
        from backend.database.system_settings_crud import is_notification_enabled

        db = SessionLocal()
        try:
            return is_notification_enabled(db, event_type)
        finally:
            db.close()
    except Exception as exc:
        logger.warning(
            "[Telegram] Could not read notification preferences: %s; enabling by default.",
            exc,
        )
        return True


def send_telegram_alert(event: SecurityEvent) -> bool:
    """Send a confirmed event to Telegram without raising into the pipeline."""
    if not _is_notification_enabled_for(event.event_type):
        logger.info(
            "[Telegram] Notifications disabled for %s; skipping alert.",
            event.event_type,
        )
        return False
    if not _is_configured():
        logger.warning(
            "[Telegram] Bot token or chat ID not configured; skipping %s alert.",
            event.event_type,
        )
        return False

    screenshot_path = (
        settings.SCREENSHOTS_DIR / event.screenshot_path
        if event.screenshot_path
        else None
    )
    caption = _build_caption(event)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            if screenshot_path and screenshot_path.exists():
                success = _send_photo(screenshot_path, caption)
            else:
                reason = (
                    "no screenshot_path set on event"
                    if not event.screenshot_path
                    else f"file not found at {screenshot_path}"
                )
                logger.warning("[Telegram] %s; sending text-only alert.", reason)
                success = _send_text(caption)

            if success:
                logger.info("[Telegram] Alert sent for %s event.", event.event_type)
                return True

            if attempt < MAX_RETRIES:
                logger.warning(
                    "[Telegram] Attempt %d/%d returned a failure response; retrying.",
                    attempt,
                    MAX_RETRIES,
                )
                time.sleep(RETRY_DELAY_SECONDS)
        except (OSError, requests.exceptions.RequestException, ValueError) as exc:
            logger.warning(
                "[Telegram] Attempt %d/%d failed: %s", attempt, MAX_RETRIES, exc
            )
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SECONDS)

    logger.error(
        "[Telegram] Failed to send alert for %s event after %d attempts.",
        event.event_type,
        MAX_RETRIES,
    )
    return False


def _send_photo(image_path: Path, caption: str) -> bool:
    url = f"{TELEGRAM_API_BASE}/bot{settings.TELEGRAM_BOT_TOKEN}/sendPhoto"
    with image_path.open("rb") as photo_file:
        response = requests.post(
            url,
            data={
                "chat_id": settings.TELEGRAM_CHAT_ID,
                "caption": caption,
                "parse_mode": "Markdown",
            },
            files={"photo": photo_file},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    return _handle_response(response)


def _send_text(text: str) -> bool:
    url = f"{TELEGRAM_API_BASE}/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    response = requests.post(
        url,
        data={
            "chat_id": settings.TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "Markdown",
        },
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    return _handle_response(response)


def _handle_response(response: requests.Response) -> bool:
    if response.status_code == 200 and response.json().get("ok"):
        return True
    logger.error(
        "[Telegram] API returned an error; status %d, body: %s",
        response.status_code,
        response.text[:500],
    )
    return False


def send_test_message() -> bool:
    """Send a text-only test message using the configured bot credentials."""
    if not _is_configured():
        print("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set in .env")
        return False

    try:
        success = _send_text(
            "✅ Surveillance system test message — Telegram integration is working."
        )
        print(
            "✅ Test message sent successfully."
            if success
            else "❌ Telegram API rejected the message."
        )
        return success
    except (OSError, requests.exceptions.RequestException, ValueError) as exc:
        print(f"❌ Could not reach Telegram API: {exc}")
        return False
