import os
from typing import List
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Telegram Settings
    TELEGRAM_BOT_TOKEN: str = ""
    ALLOWED_TELEGRAM_USER_IDS: str = ""
    DEFAULT_TELEGRAM_CHAT_ID: str = "-5540322388"
    ENABLE_TELEGRAM_POLLING: bool = False

    # AI Configuration (Universal OpenAI-Compatible)
    AI_BASE_URL: str = "https://api.openai.com/v1"
    AI_API_KEY: str = ""
    AI_MODEL: str = "gpt-4o-mini"
    AI_TEMPERATURE: float = 0.2

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/mikrotik_bot.db"

    # Security
    SECRET_KEY: str = "default_secret_key_change_in_production_32_bytes_len"

    # App Settings
    HOST: str = "0.0.0.0"
    PORT: int = 3010
    LOG_LEVEL: str = "INFO"
    APPROVAL_TIMEOUT_MINUTES: int = 5
    METRICS_RETENTION_DAYS: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def allowed_user_ids(self) -> List[int]:
        """Parse comma-separated Telegram User/Chat IDs into a list of integers."""
        if not self.ALLOWED_TELEGRAM_USER_IDS.strip():
            return []
        ids = []
        for item in self.ALLOWED_TELEGRAM_USER_IDS.split(","):
            cleaned = item.strip()
            try:
                ids.append(int(cleaned))
            except ValueError:
                pass
        return ids


settings = Settings()
