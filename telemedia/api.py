"""FastAPI application exposing the Telegram collection workflow."""

from __future__ import annotations

import asyncio
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json

from .analysis import ContentAnalyzer
from .config import Settings, get_logger, get_media_directory, get_settings
from .schemas import CollectedItem, FinalResponse, GlobalAnalysis, KeywordCount, PageData, TelegramMessage
from .telegram_collector import TelegramCollector
from .web_scraper import WebScraper

settings: Settings = get_settings()
logger = get_logger("telemedia.api")
collector = TelegramCollector(settings)
scraper = WebScraper(settings)
analyzer = ContentAnalyzer()

app = FastAPI(title="TeleMediaBot Service", version="2.0.0",
              description="Telegram + web scraping collector")

BASE_DIR = Path(__file__).resolve().parent
MEDIA_DIR = get_media_directory(settings)
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/media", StaticFiles(directory=str(MEDIA_DIR),
          check_dir=False), name="media")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


@app.on_event("startup")
async def startup_event() -> None:  # pragma: no cover - lifecycle hook
    await collector.connect()
    await scraper.start()


@app.on_event("shutdown")
async def shutdown_event() -> None:  # pragma: no cover - lifecycle hook
    await scraper.close()
    await collector.disconnect()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


async def run_collection(
    group: str | None = None,
    limit: int | None = None,
) -> FinalResponse:
    try:
        messages = await collector.fetch_group_messages(group=group, limit=limit)
    except ValueError as exc:
        logger.warning("Telegram group lookup failed: %s", exc)
        raise HTTPException(
            status_code=404, detail="Telegram group not found or inaccessible.") from exc
    except Exception as exc:  # pragma: no cover - network failure
        logger.error("Telegram fetch failed: %s", exc)
        raise HTTPException(
            status_code=502, detail="Failed to fetch Telegram messages") from exc

    url_pairs: list[tuple[int, str]] = []
    message_map: dict[int, TelegramMessage] = {}
    for message in messages:
        if not message.urls:
            continue
        message_map[message.message_id] = message
        for url in message.urls:
            url_pairs.append((message.message_id, url))

    if not url_pairs:
        logger.info("No URLs found in the latest messages")
        return FinalResponse(
            group_id=group or settings.group,
            collected_at=datetime.now(timezone.utc),
            items=[],
            messages=messages,
            global_analysis=GlobalAnalysis(),
        )

    semaphore = asyncio.Semaphore(settings.request_concurrency)

    async def scrape_with_limit(url: str) -> PageData:
        async with semaphore:
            return await scraper.scrape_page(url)

    scrape_tasks = [scrape_with_limit(url) for _, url in url_pairs]
    scrape_results = await asyncio.gather(*scrape_tasks, return_exceptions=True)

    items: List[CollectedItem] = []
    keyword_counter: Counter[str] = Counter()
    texts_for_similarity: list[str] = []

    for (message_id, url), result in zip(url_pairs, scrape_results):
        page: PageData
        if isinstance(result, Exception):  # pragma: no cover - network failure
            page = PageData(url=url, error=str(result))
        else:
            page = result
        telegram_message = message_map.get(message_id)
        if telegram_message is None:
            continue
        if page.content:
            analysis_result, token_counts = analyzer.analyze_content(
                page.content)
            page.analysis = analysis_result
            keyword_counter.update(token_counts)
            if settings.enable_similarity:
                texts_for_similarity.append(page.content)
        items.append(
            CollectedItem(
                telegram=telegram_message,
                page=page,
            )
        )

    similarity_matrix: list[list[float]] = []
    if settings.enable_similarity and texts_for_similarity:
        similarity_matrix = analyzer.compute_similarity(texts_for_similarity)

    most_common = [KeywordCount(word=word, count=count)
                   for word, count in keyword_counter.most_common(15)]

    response = FinalResponse(
        group_id=group or settings.group,
        collected_at=datetime.now(timezone.utc),
        items=items,
        messages=messages,
        global_analysis=GlobalAnalysis(
            similarity_matrix=similarity_matrix,
            most_frequent_keywords=most_common,
        ),
    )
    return response


def _fallback_group_choices(preferred_group: str | None = None) -> list[dict[str, str]]:
    fallback_values = []
    seen: set[str] = set()
    for candidate in [preferred_group, settings.group, *settings.group_options]:
        if not candidate or candidate in seen:
            continue
        fallback_values.append({"value": candidate, "label": candidate})
        seen.add(candidate)
    if not fallback_values:
        fallback_values.append(
            {"value": settings.group, "label": settings.group})
    return fallback_values


async def get_group_choices(preferred_group: str | None = None) -> list[dict[str, str]]:
    try:
        groups = await collector.list_joined_groups()
        if groups:
            return groups
    except Exception as exc:  # pragma: no cover - Telethon/connection issues
        logger.warning("Failed to load account groups: %s", exc)
    return _fallback_group_choices(preferred_group)


@app.get("/collect/telegram-group", response_model=FinalResponse)
async def collect_telegram_group(
    group: str | None = Query(
        default=None, description="Override the default Telegram group"),
    limit: int | None = Query(
        default=None, ge=1, le=200, description="Number of messages to inspect"),
) -> FinalResponse:
    return await run_collection(group=group, limit=limit)


@app.get("/groups")
async def list_available_groups() -> dict[str, list[dict[str, str]]]:
    """Return the configured group options for the dropdown selector."""

    groups = await get_group_choices()
    return {"groups": groups}


@app.get("/api/stats/summary")
async def get_stats_summary() -> dict:
    """Return quick stats for the dashboard."""
    try:
        # Get joined groups count
        groups = await collector.list_joined_groups()
        groups_count = len(groups)

        # For now, return placeholder values for messages and media
        # In a real implementation, you'd query a database or cache
        return {
            "groups_count": groups_count,
            "messages_today": 0,  # TODO: Implement message tracking
            "total_media": 0,  # TODO: Implement media tracking
            "last_activity": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as exc:
        logger.warning("Failed to fetch stats: %s", exc)
        return {
            "groups_count": 0,
            "messages_today": 0,
            "total_media": 0,
            "last_activity": None,
        }


@app.get("/stream/telegram-group")
async def stream_telegram_group(
    group: str | None = Query(
        default=None, description="Override the default Telegram group"),
    limit: int | None = Query(
        default=None, ge=1, le=200, description="Number of messages to inspect"),
) -> StreamingResponse:
    """Stream Telegram messages and scraped pages as Server-Sent Events."""

    async def event_generator():
        try:
            # Fetch Telegram messages
            try:
                messages = await collector.fetch_group_messages(group=group, limit=limit)
            except ValueError as exc:
                logger.warning("Telegram group lookup failed: %s", exc)
                error_data = {
                    "error": "Telegram group not found or inaccessible."}
                yield f"data: {json.dumps(error_data)}\n\n"
                return
            except Exception as exc:
                logger.error("Telegram fetch failed: %s", exc)
                error_data = {"error": "Failed to fetch Telegram messages"}
                yield f"data: {json.dumps(error_data)}\n\n"
                return

            # Send initial metadata
            meta_data = {
                "type": "meta",
                "group_id": group or settings.group,
                "total_messages": len(messages),
                "collected_at": datetime.now(timezone.utc).isoformat(),
            }
            yield f"data: {json.dumps(meta_data)}\n\n"

            # Prepare URL pairs
            url_pairs: list[tuple[int, str]] = []
            message_map: dict[int, TelegramMessage] = {}
            for message in messages:
                if not message.urls:
                    continue
                message_map[message.message_id] = message
                for url in message.urls:
                    url_pairs.append((message.message_id, url))

            if not url_pairs:
                final_data = {
                    "type": "complete",
                    "messages": [msg.model_dump(mode="json") for msg in messages],
                    "items": [],
                    "global_analysis": GlobalAnalysis().model_dump(mode="json"),
                }
                yield f"data: {json.dumps(final_data)}\n\n"
                return

            # Process each URL and stream results
            semaphore = asyncio.Semaphore(settings.request_concurrency)
            keyword_counter: Counter[str] = Counter()
            texts_for_similarity: list[str] = []
            items: List[CollectedItem] = []

            async def scrape_and_yield(message_id: int, url: str, index: int):
                async with semaphore:
                    page = await scraper.scrape_page(url)
                    telegram_message = message_map.get(message_id)
                    if telegram_message is None:
                        return None

                    if page.content:
                        analysis_result, token_counts = analyzer.analyze_content(
                            page.content)
                        page.analysis = analysis_result
                        keyword_counter.update(token_counts)
                        if settings.enable_similarity:
                            texts_for_similarity.append(page.content)

                    item = CollectedItem(telegram=telegram_message, page=page)
                    items.append(item)

                    # Stream this item immediately
                    item_data = {
                        "type": "item",
                        "index": index,
                        "data": item.model_dump(mode='json'),
                    }
                    return json.dumps(item_data)

            # Process all URLs concurrently and yield as they complete
            tasks = [scrape_and_yield(msg_id, url, idx)
                     for idx, (msg_id, url) in enumerate(url_pairs)]

            for coro in asyncio.as_completed(tasks):
                try:
                    result = await coro
                    if result:
                        yield f"data: {result}\n\n"
                except Exception as exc:
                    logger.error("Failed to scrape URL: %s", exc)

            # Compute global analysis
            similarity_matrix: list[list[float]] = []
            if settings.enable_similarity and texts_for_similarity:
                similarity_matrix = analyzer.compute_similarity(
                    texts_for_similarity)

            most_common = [KeywordCount(word=word, count=count)
                           for word, count in keyword_counter.most_common(15)]

            global_analysis = GlobalAnalysis(
                similarity_matrix=similarity_matrix,
                most_frequent_keywords=most_common,
            )

            # Send completion with all messages and global analysis
            final_data = {
                "type": "complete",
                "messages": [msg.model_dump(mode='json') for msg in messages],
                "global_analysis": global_analysis.model_dump(mode='json'),
            }
            yield f"data: {json.dumps(final_data)}\n\n"

        except Exception as exc:
            logger.error("Stream error: %s", exc)
            error_data = {"type": "error", "error": str(exc)}
            yield f"data: {json.dumps(error_data)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    group: str | None = Query(
        default=None, description="Override the default Telegram group"),
    limit: int | None = Query(
        default=None, ge=1, le=200, description="Number of messages to inspect"),
) -> HTMLResponse:
    """Dashboard page - displays streaming message collection interface."""

    group_choices = await get_group_choices(group or settings.group)

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "group": group or settings.group,
            "limit": limit or settings.default_message_limit,
            "error_message": None,
            "group_options": group_choices,
            "active_page": "dashboard",
        },
    )


@app.get("/messages", response_class=HTMLResponse)
async def messages_page(request: Request) -> HTMLResponse:
    """Messages page - view and filter all collected messages."""
    return templates.TemplateResponse(
        "messages.html",
        {
            "request": request,
            "active_page": "messages",
        },
    )


@app.get("/media", response_class=HTMLResponse)
async def media_page(request: Request) -> HTMLResponse:
    """Media page - view and manage all media files."""
    return templates.TemplateResponse(
        "media.html",
        {
            "request": request,
            "active_page": "media",
        },
    )


@app.get("/groups", response_class=HTMLResponse)
async def groups_page(request: Request) -> HTMLResponse:
    """Groups page - view all joined Telegram groups."""
    return templates.TemplateResponse(
        "groups.html",
        {
            "request": request,
            "active_page": "groups",
        },
    )


@app.get("/channels", response_class=HTMLResponse)
async def channels_page(request: Request) -> HTMLResponse:
    """Channels page - view all subscribed Telegram channels."""
    return templates.TemplateResponse(
        "channels.html",
        {
            "request": request,
            "active_page": "channels",
        },
    )


@app.get("/bot-tools", response_class=HTMLResponse)
async def bot_tools_page(request: Request) -> HTMLResponse:
    """Bot Tools page - automation and messaging features."""
    return templates.TemplateResponse(
        "bot_tools.html",
        {
            "request": request,
            "active_page": "bot-tools",
        },
    )


@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request) -> HTMLResponse:
    """Admin page - group moderation and user management."""
    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "active_page": "admin",
        },
    )


@app.get("/analytics", response_class=HTMLResponse)
async def analytics_page(request: Request) -> HTMLResponse:
    """Analytics page - charts, reports, and statistics."""
    return templates.TemplateResponse(
        "analytics.html",
        {
            "request": request,
            "active_page": "analytics",
        },
    )
