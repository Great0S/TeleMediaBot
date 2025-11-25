"""Telegram collection layer built on Telethon."""

from __future__ import annotations

import asyncio
import mimetypes
import re
from pathlib import Path
from typing import Dict, List, Optional

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
        self._dialog_lookup: Dict[str, object] = {}
        self._label_lookup: Dict[str, object] = {}

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

    async def list_joined_groups(self, limit: int = 200, refresh: bool = True) -> List[dict[str, str]]:
        """Return the list of groups/channels the user account has joined."""

        await self.connect()
        groups: List[dict[str, str]] = []
        seen: set[str] = set()

        # Only clear lookups if explicitly refreshing
        if refresh:
            self._dialog_lookup.clear()
            self._label_lookup.clear()

        async for dialog in self._client.iter_dialogs(limit=limit):
            if not (dialog.is_group or dialog.is_channel):
                continue
            entity = dialog.entity
            if entity is None:
                continue

            username = getattr(entity, "username", None)
            raw_id = getattr(entity, "id", None)
            peer_id: Optional[str] = None
            if raw_id is not None:
                # Align with how Telegram represents chat/channel ids in clients
                if getattr(entity, "megagroup", False) or getattr(entity, "gigagroup", False) or dialog.is_channel:
                    peer_id = f"-100{raw_id}"
                else:
                    peer_id = str(raw_id)

            value = username or peer_id
            if not value or value in seen:
                continue

            label = dialog.name or getattr(entity, "title", None) or value
            self._dialog_lookup[value] = entity
            self._label_lookup[label.casefold()] = entity
            groups.append({"value": value, "label": label})
            seen.add(value)

        if not groups:
            fallback = self.settings.group
            groups.append({"value": fallback, "label": fallback})

        return groups

    async def fetch_group_messages(self, group: Optional[str] = None, limit: Optional[int] = None) -> List[TelegramMessage]:
        """Fetch the latest messages from the configured Telegram group."""

        await self.connect()
        target_key = group or self.settings.group
        target = await self._resolve_target(target_key)

        # Validate target is a group/channel, not a user (defensive check)
        from telethon.tl.types import User
        if isinstance(target, User):
            raise ValueError(
                f"'{target_key}' resolved to a User account, not a group or channel. "
                f"Please specify a group/channel username or ID."
            )

        fetch_limit = limit or self.settings.default_message_limit
        entity_type = type(target).__name__
        self.logger.info("Fetching %s messages from %s (%s)",
                         fetch_limit, target_key, entity_type)

        try:
            self._download_budget = max(0, self.settings.media_download_limit)
            messages: List[TelegramMessage] = []
            async for message in self._client.iter_messages(target, limit=fetch_limit):
                text = self._extract_text(message)
                if not text and not message.media:
                    continue
                attachments = await self._extract_attachments(message)
                telegram_message = TelegramMessage(
                    message_id=message.id,
                    date=message.date,
                    text=text,
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

    async def _resolve_target(self, target_key: str) -> object:
        # Populate lookup cache if empty (don't clear existing entries)
        if not self._dialog_lookup:
            await self.list_joined_groups(refresh=False)

        target = self._dialog_lookup.get(target_key)
        if target:
            return target

        if isinstance(target_key, str):
            label_target = self._label_lookup.get(target_key.casefold())
            if label_target:
                return label_target

        # Last resort: try Telethon's entity resolution
        try:
            entity = await self._client.get_entity(target_key)
            # Validate it's not a User before caching
            from telethon.tl.types import User
            if isinstance(entity, User):
                raise ValueError(
                    f"'{target_key}' resolved to a User account (@{getattr(entity, 'username', 'unknown')}), "
                    f"not a group or channel. Please specify a valid group/channel."
                )
            if isinstance(target_key, str):
                self._dialog_lookup[target_key] = entity
            return entity
        except ValueError:
            raise
        except Exception as exc:  # pragma: no cover - Telethon resolution errors
            raise ValueError(
                f"Telegram group '{target_key}' not found or inaccessible") from exc

    def _extract_text(self, message: Message) -> str:
        return message.message or getattr(message, "raw_text", None) or ""

    def _extract_urls(self, message: Message) -> List[str]:
        text = self._extract_text(message)
        return _URL_PATTERN.findall(text)

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
