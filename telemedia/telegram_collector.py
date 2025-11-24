"""Telegram collection layer built on Telethon."""

from __future__ import annotations

import asyncio
import mimetypes
import re
from pathlib import Path
from typing import List, Optional

from telethon import TelegramClient
from telethon.errors import RPCError
from telethon.tl.custom.message import Message

from .config import Settings, get_logger, get_media_directory
from .schemas import TelegramAttachment, TelegramMessage

_URL_PATTERN = re.compile(
    r"((?:https?://)(?:[\w.-]+)(?:/[\w\-./?%&=+#]*)?)",
    re.IGNORECASE,
)


class TelegramCollector:
    """Encapsulates Telethon client lifecycle and message retrieval."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._client = TelegramClient(
            session=settings.session_name,
            api_id=settings.api_id,
            api_hash=settings.api_hash,
            sequential_updates=False,
        )
        self.logger = get_logger("telemedia.collector")
        self._lock = asyncio.Lock()
        self.media_dir = get_media_directory(self.settings)
        self.thumbnail_dir = self.media_dir / "thumbnails"
        self.thumbnail_dir.mkdir(parents=True, exist_ok=True)
        self.original_dir = self.media_dir / "originals"
        self.original_dir.mkdir(parents=True, exist_ok=True)
        self._download_budget: int = 0

    async def connect(self) -> None:
        """Ensure the client is connected and authorized."""

        async with self._lock:
            if self._client.is_connected():
                return
            self.logger.info(
                "Connecting to Telegram as user session '%s'", self.settings.session_name)
            await self._client.connect()
            if not await self._client.is_user_authorized():
                raise RuntimeError(
                    "The Telethon session is not authorized. Please run the login flow once using telethon."  # noqa: EM102
                )
            self.logger.info("Telegram client connected")

    async def disconnect(self) -> None:
        async with self._lock:
            if self._client.is_connected():
                await self._client.disconnect()
                self.logger.info("Telegram client disconnected")

    async def fetch_group_messages(self, group: Optional[str] = None, limit: Optional[int] = None) -> List[TelegramMessage]:
        """Fetch the latest messages from the configured Telegram group."""

        await self.connect()
        target = group or self.settings.group
        fetch_limit = limit or self.settings.default_message_limit
        self.logger.info("Fetching %s messages from %s", fetch_limit, target)

        try:
            self._download_budget = max(0, self.settings.media_download_limit)
            messages: List[TelegramMessage] = []
            async for message in self._client.iter_messages(target, limit=fetch_limit):
                if not message.message:
                    continue
                attachments = await self._extract_attachments(message)
                telegram_message = TelegramMessage(
                    message_id=message.id,
                    date=message.date,
                    text=message.message,
                    urls=self._extract_urls(message),
                    attachments=attachments,
                )
                messages.append(telegram_message)
        except RPCError as exc:  # pragma: no cover - network failure
            self.logger.error("Failed to read messages: %s", exc)
            raise

        messages.reverse()  # chronological order from oldest to newest
        self.logger.info("Fetched %s messages", len(messages))
        return messages

    def _extract_urls(self, message: Message) -> List[str]:
        text = message.message or ""
        return [match[0] for match in _URL_PATTERN.findall(text)]

    async def _extract_attachments(self, message: Message) -> List[TelegramAttachment]:
        if not message.media:
            return []

        file = getattr(message, "file", None)
        width, height = self._extract_dimensions(message)
        duration = self._extract_duration(message)
        mime_type = getattr(file, "mime_type", None)

        attachment = TelegramAttachment(
            media_type=message.media.__class__.__name__,
            file_name=getattr(file, "name", None),
            mime_type=mime_type,
            size_bytes=getattr(file, "size", None),
            width=width,
            height=height,
            duration_seconds=duration,
        )

        attachment.thumbnail_url = await self._download_thumbnail(message, mime_type)
        if self._should_download_full_media(mime_type, file):
            media_url = await self._download_full_media(message, mime_type)
            if media_url:
                attachment.media_url = media_url
                if self._download_budget > 0:
                    self._download_budget -= 1
        return [attachment]

    def _extract_dimensions(self, message: Message) -> tuple[Optional[int], Optional[int]]:
        width = getattr(message.media, "w", None) if message.media else None
        height = getattr(message.media, "h", None) if message.media else None
        document = getattr(message.media, "document",
                           None) if message.media else None

        if (width is not None) and (height is not None):
            return width, height

        attributes = getattr(document, "attributes", None)
        if attributes:
            for attr in attributes:
                width = width or getattr(
                    attr, "w", getattr(attr, "width", None))
                height = height or getattr(
                    attr, "h", getattr(attr, "height", None))
                if width is not None and height is not None:
                    break
        return width, height

    def _extract_duration(self, message: Message) -> Optional[int]:
        if not message.media:
            return None

        duration = getattr(message.media, "duration", None)
        if duration is not None:
            return self._coerce_duration(duration)

        document = getattr(message.media, "document", None)
        attributes = getattr(document, "attributes", None)
        if attributes:
            for attr in attributes:
                if hasattr(attr, "duration"):
                    coerced = self._coerce_duration(attr.duration)
                    if coerced is not None:
                        return coerced
        return None

    def _coerce_duration(self, value: Optional[float]) -> Optional[int]:
        if value is None:
            return None
        try:
            rounded = int(round(float(value)))
        except (TypeError, ValueError):
            return None
        return max(0, rounded)

    async def _download_thumbnail(self, message: Message, mime_type: Optional[str]) -> Optional[str]:
        if not message.media:
            return None

        if mime_type and not mime_type.startswith(("image", "video")):
            return None

        suffix = ".png" if mime_type and "png" in mime_type else ".jpg"
        filename = f"{message.id}_{int(message.date.timestamp())}{suffix}"
        target_path = self.thumbnail_dir / filename
        if target_path.exists():
            return self._public_url_for(target_path)

        try:
            downloaded_path = await message.download_media(file=str(target_path), thumb=-1)
        except Exception as exc:  # pragma: no cover - network/IO edge
            self.logger.debug("Skipping thumbnail for %s: %s", message.id, exc)
            return None

        if not downloaded_path:
            return None

        return self._public_url_for(Path(downloaded_path))

    async def _download_full_media(self, message: Message, mime_type: Optional[str]) -> Optional[str]:
        if not message.media:
            return None

        extension = self._resolve_extension(message, mime_type)
        filename = f"{message.id}_{int(message.date.timestamp())}{extension}"
        target_path = self.original_dir / filename
        if target_path.exists():
            return self._public_url_for(target_path)

        try:
            downloaded_path = await message.download_media(file=str(target_path))
        except Exception as exc:  # pragma: no cover - network/IO edge
            self.logger.debug(
                "Skipping full media for %s: %s", message.id, exc)
            return None

        if not downloaded_path:
            return None

        return self._public_url_for(Path(downloaded_path))

    def _resolve_extension(self, message: Message, mime_type: Optional[str]) -> str:
        file = getattr(message, "file", None)
        ext = getattr(file, "ext", None)
        if isinstance(ext, str) and ext:
            return ext if ext.startswith(".") else f".{ext}"

        if mime_type:
            guessed = mimetypes.guess_extension(
                mime_type.split(";")[0].strip())
            if guessed:
                return guessed

        return ".bin"

    def _public_url_for(self, file_path: Path) -> str:
        try:
            relative = file_path.resolve().relative_to(self.media_dir.resolve())
        except ValueError:
            relative = Path(file_path.name)
        return f"/media/{relative.as_posix()}"

    def _should_download_full_media(self, mime_type: Optional[str], file_obj: Optional[object]) -> bool:
        if not self.settings.enable_media_downloads:
            return False
        if mime_type and not mime_type.startswith(("image", "video")):
            return False
        if self._download_budget <= 0:
            return False
        size = getattr(file_obj, "size", None)
        if size and size > self.settings.media_max_bytes:
            self.logger.debug(
                "Skipping media download (size %s exceeds cap %s)",
                size,
                self.settings.media_max_bytes,
            )
            return False
        return True


collector: Optional[TelegramCollector] = None
