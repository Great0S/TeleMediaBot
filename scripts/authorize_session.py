from __future__ import annotations

import asyncio
import sys
from getpass import getpass
from pathlib import Path

from telethon.errors import SessionPasswordNeededError
from telethon.sync import TelegramClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from telemedia.config import get_logger, get_settings  # noqa: E402


async def ensure_authorized() -> None:
    settings = get_settings()
    logger = get_logger("telemedia.auth")

    logger.info("Using session '%s'", settings.session_name)
    client = TelegramClient(settings.session_name,
                            settings.api_id, settings.api_hash)

    async with client:
        if await client.is_user_authorized():
            logger.info("Session already authorized; nothing to do.")
            return

        phone = input(
            "Enter the Telegram account phone number (international format): ").strip()
        if not phone:
            raise RuntimeError(
                "Phone number is required to authorize the session.")

        await client.send_code_request(phone)
        code = input("Enter the verification code you received: ").strip()
        try:
            await client.sign_in(phone=phone, code=code)
        except SessionPasswordNeededError:
            password = getpass("Two-factor password required: ")
            await client.sign_in(password=password)

        logger.info("Session authorization complete.")


def main() -> None:
    asyncio.run(ensure_authorized())


if __name__ == "__main__":
    main()
