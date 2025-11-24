from __future__ import annotations

import unittest
from contextlib import ExitStack
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from telemedia import config
from telemedia.api import app, collector, scraper
from telemedia.schemas import PageData, TelegramAttachment, TelegramMessage


class TestAPI(unittest.TestCase):
    """Integration-style tests for the FastAPI application."""

    def test_collect_endpoint_returns_enriched_payload(self) -> None:
        sample_message = TelegramMessage(
            message_id=1,
            date=datetime(2024, 5, 1, tzinfo=timezone.utc),
            text="Check this https://example.com/article",
            urls=["https://example.com/article"],
            attachments=[
                TelegramAttachment(
                    media_type="Photo",
                    file_name="promo.png",
                    mime_type="image/png",
                    size_bytes=2048,
                    thumbnail_url="/media/thumbnails/promo.png",
                    media_url="/media/originals/promo.png",
                )
            ],
        )

        sample_page = PageData(
            url="https://example.com/article",
            title="Example",
            description="Example description",
            content="Sale sale discount product",
            content_snippet="Sale sale discount product",
        )

        with ExitStack() as stack:
            stack.enter_context(patch.object(
                collector, "connect", new=AsyncMock()))
            stack.enter_context(patch.object(
                scraper, "start", new=AsyncMock()))
            stack.enter_context(patch.object(
                scraper, "close", new=AsyncMock()))
            stack.enter_context(patch.object(
                collector, "disconnect", new=AsyncMock()))
            stack.enter_context(patch.object(
                collector, "fetch_group_messages", new=AsyncMock(return_value=[sample_message])))
            stack.enter_context(patch.object(
                scraper, "scrape_page", new=AsyncMock(return_value=sample_page)))

            with TestClient(app) as client:
                response = client.get(
                    "/collect/telegram-group", params={"limit": 1})

        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertEqual(payload["group_id"], config.settings.group)
        self.assertTrue(payload["items"],
                        "Expected at least one collected item")
        self.assertTrue(payload["messages"],
                        "Raw messages should be included in the response")
        self.assertEqual(payload["messages"][0]["message_id"],
                         sample_message.message_id)
        self.assertEqual(len(payload["messages"][0]["attachments"]), 1)
        self.assertEqual(
            payload["messages"][0]["attachments"][0]["thumbnail_url"],
            "/media/thumbnails/promo.png",
        )
        self.assertEqual(
            payload["messages"][0]["attachments"][0]["media_url"],
            "/media/originals/promo.png",
        )
        item = payload["items"][0]
        self.assertEqual(item["telegram"]["message_id"],
                         sample_message.message_id)
        self.assertEqual(item["page"]["url"], sample_page.url)
        self.assertGreater(item["page"]["analysis"]["total_tokens"], 0)
        self.assertTrue(payload["global_analysis"]["most_frequent_keywords"],
                        "Keyword summary should not be empty")


if __name__ == "__main__":
    unittest.main()
