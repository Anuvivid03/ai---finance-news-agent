"""
Telegram notification module.
"""

from __future__ import annotations

import logging
import os

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

TELEGRAM_API_URL = (
    f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
)


def send_telegram_message(message: str) -> bool:
    """Send a text message to the configured Telegram chat."""

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.error("Telegram configuration is missing.")
        return False

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
    }

    try:
        response = requests.post(
            TELEGRAM_API_URL,
            json=payload,
            timeout=30,
        )

        response.raise_for_status()

        logger.info("Telegram message sent successfully.")
        return True

    except requests.RequestException as exc:
        logger.error(
            "Failed to send Telegram message: %s",
            exc,
        )
        return False
