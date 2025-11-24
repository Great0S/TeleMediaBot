"""Non-AI web scraping helpers."""

from __future__ import annotations

from typing import Optional

import httpx
from bs4 import BeautifulSoup

from .config import Settings, get_logger
from .schemas import PageData


class WebScraper:
    """Fetches and parses webpages with graceful error handling."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.logger = get_logger("telemedia.scraper")
        self._client: Optional[httpx.AsyncClient] = None
        self._snippet_length = 280
        self._content_limit = 6000

    async def start(self) -> None:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.settings.http_timeout,
                follow_redirects=True,
                headers={"User-Agent": self.settings.user_agent},
            )

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def scrape_page(self, url: str) -> PageData:
        if self._client is None:
            await self.start()
        assert self._client is not None

        try:
            response = await self._client.get(url)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            self.logger.warning("HTTP error for %s: %s", url, exc)
            return PageData(url=url, error=str(exc))

        soup = BeautifulSoup(response.text, "html.parser")
        title = self._get_title(soup)
        description = self._get_description(soup)
        content = self._extract_content(soup)
        snippet = content[: self._snippet_length].strip() if content else None

        page = PageData(
            url=url,
            title=title,
            description=description,
            content=content,
            content_snippet=snippet,
        )
        self.logger.info("Scraped %s (title='%s')", url, title)
        return page

    def _get_title(self, soup: BeautifulSoup) -> Optional[str]:
        if soup.title and soup.title.string:
            return soup.title.string.strip()
        return None

    def _get_description(self, soup: BeautifulSoup) -> Optional[str]:
        tag = soup.find("meta", attrs={"name": "description"})
        if tag and tag.get("content"):
            return tag["content"].strip()
        return None

    def _extract_content(self, soup: BeautifulSoup) -> Optional[str]:
        paragraphs = [p.get_text(strip=True)
                      for p in soup.find_all("p") if p.get_text(strip=True)]
        if not paragraphs:
            return None
        content = "\n".join(paragraphs)
        if len(content) > self._content_limit:
            content = content[: self._content_limit].rstrip() + "…"
        return content
