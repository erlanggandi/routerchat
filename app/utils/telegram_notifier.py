import logging
import io
import httpx
from typing import Optional, Dict, Any
from config.settings import settings

logger = logging.getLogger(__name__)


class TelegramNotifier:
    def __init__(self):
        self.base_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}"

    async def send_message(
        self,
        text: str,
        chat_id: Optional[str] = None,
        parse_mode: str = "Markdown",
        reply_markup: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Send message directly via Telegram HTTP API."""
        if not settings.TELEGRAM_BOT_TOKEN:
            logger.warning("TELEGRAM_BOT_TOKEN is not configured.")
            return False

        target_chat = chat_id or settings.DEFAULT_TELEGRAM_CHAT_ID
        payload: Dict[str, Any] = {
            "chat_id": target_chat,
            "text": text,
            "parse_mode": parse_mode,
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(f"{self.base_url}/sendMessage", json=payload)
                if resp.status_code != 200:
                    logger.error(f"Telegram API error: {resp.text}")
                    return False
                return True
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False

    async def send_photo(
        self,
        photo_bytes: io.BytesIO,
        caption: Optional[str] = None,
        chat_id: Optional[str] = None,
        parse_mode: str = "Markdown",
    ) -> bool:
        """Send photo chart directly via Telegram HTTP API."""
        if not settings.TELEGRAM_BOT_TOKEN:
            return False

        target_chat = chat_id or settings.DEFAULT_TELEGRAM_CHAT_ID
        photo_bytes.seek(0)
        files = {"photo": ("chart.png", photo_bytes, "image/png")}
        data: Dict[str, Any] = {"chat_id": target_chat}
        if caption:
            data["caption"] = caption
            data["parse_mode"] = parse_mode

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(f"{self.base_url}/sendPhoto", data=data, files=files)
                if resp.status_code != 200:
                    logger.error(f"Telegram API sendPhoto error: {resp.text}")
                    return False
                return True
        except Exception as e:
            logger.error(f"Failed to send Telegram photo: {e}")
            return False


telegram_notifier = TelegramNotifier()
