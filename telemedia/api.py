"""FastAPI application exposing the Telegram collection workflow."""

from __future__ import annotations

import asyncio
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

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


@app.get("/collect/telegram-group", response_model=FinalResponse)
async def collect_telegram_group(
    group: str | None = Query(
        default=None, description="Override the default Telegram group"),
    limit: int | None = Query(
        default=None, ge=1, le=200, description="Number of messages to inspect"),
) -> FinalResponse:
    return await run_collection(group=group, limit=limit)


@app.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    group: str | None = Query(
        default=None, description="Override the default Telegram group"),
    limit: int | None = Query(
        default=None, ge=1, le=200, description="Number of messages to inspect"),
) -> HTMLResponse:
    error_message: str | None = None
    try:
        result = await run_collection(group=group, limit=limit)
    except HTTPException as exc:
        error_message = exc.detail if isinstance(
            exc.detail, str) else str(exc.detail)
        result = FinalResponse(
            group_id=group or settings.group,
            collected_at=datetime.now(timezone.utc),
            items=[],
            messages=[],
            global_analysis=GlobalAnalysis(),
        )
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "result": result,
            "group": group or settings.group,
            "limit": limit or settings.default_message_limit,
            "error_message": error_message,
        },
    )
