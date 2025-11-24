"""Application configuration and logging helpers."""

from __future__ import annotations

import logging
from functools import lru_cache
from logging.config import dictConfig
from pathlib import Path

from pydantic import Field, PositiveInt
from pydantic_settings import BaseSettings, SettingsConfigDict

try:  # Reuse the existing richer logging configuration when available.
    from config.logger import log_config
except Exception:  # pragma: no cover - fallback for minimal environments
    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "[%(asctime)s:%(levelname)s:%(name)s] %(message)s",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "level": "INFO",
            }
        },
        "root": {
            "handlers": ["console"],
            "level": "INFO",
        },
    }


dictConfig(log_config)


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a configured logger scoped to the provided name."""

    return logging.getLogger(name or "telemedia")


class Settings(BaseSettings):
    """Centralized configuration for the TeleMedia service."""

    api_id: int = Field(..., alias="TELEGRAM_API_ID")
    api_hash: str = Field(..., alias="TELEGRAM_API_HASH")
    session_name: str = Field("telemedia_user", alias="TELEGRAM_SESSION_NAME")
    group: str = Field(..., alias="TELEGRAM_GROUP",
                       description="Default Telegram group username or id")
    default_message_limit: PositiveInt = Field(
        30, alias="DEFAULT_MESSAGE_LIMIT")
    http_timeout: float = Field(
        12.0, alias="HTTP_TIMEOUT", description="HTTP timeout in seconds")
    request_concurrency: PositiveInt = Field(5, alias="REQUEST_CONCURRENCY")
    user_agent: str = Field(
        "TeleMediaBot/2.0 (+https://github.com/Great0S/TeleMediaBot)",
        alias="HTTP_USER_AGENT",
    )
    enable_similarity: bool = Field(True, alias="ENABLE_SIMILARITY")
    media_storage_dir: str = Field(
        "media",
        alias="MEDIA_STORAGE_DIR",
        description="Directory (absolute or relative to project root) where media thumbnails are cached",
    )
    enable_media_downloads: bool = Field(
        True,
        alias="ENABLE_MEDIA_DOWNLOADS",
        description="Download original media assets (images/videos) for the dashboard",
    )
    media_max_bytes: int = Field(
        10 * 1024 * 1024,
        alias="MEDIA_MAX_BYTES",
        description="Skip downloading media larger than this many bytes",
    )
    media_download_limit: int = Field(
        6,
        alias="MEDIA_DOWNLOAD_LIMIT",
        description="Maximum number of full media downloads per collection run",
    )

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance so the app shares a single config."""

    return Settings()


settings = get_settings()

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def get_media_directory(config: Settings | None = None) -> Path:
    """Ensure and return the directory that stores cached media thumbnails."""

    cfg = config or get_settings()
    media_path = Path(cfg.media_storage_dir)
    if not media_path.is_absolute():
        media_path = PROJECT_ROOT / media_path
    media_path.mkdir(parents=True, exist_ok=True)
    return media_path
