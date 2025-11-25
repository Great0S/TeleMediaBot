# TeleMediaBot (v2)

TeleMediaBot has been refactored into a modern, modular backend that collects URLs from Telegram groups, scrapes the linked webpages, performs deterministic keyword analysis, and exposes the results through a FastAPI service.

## Highlights

- **Telethon user client** for authenticated Telegram access.
- **Async HTTP scraping** with graceful error handling.
- **Keyword analytics** (token counts, TF–IDF similarity) without AI/LLM dependencies.
- **FastAPI** endpoint that returns clean JSON ready for automation tools such as n8n.
- Clear module boundaries so new collectors, scrapers, or analyzers can be added later.

## Requirements

- Python 3.10+
- Telegram API ID + hash and an existing Telethon session file (run `Telethon` login once).

## Installation

```bash
git clone https://github.com/Great0S/TeleMediaBot.git
cd TeleMediaBot
python -m venv .venv
.venv\Scripts\activate  # Linux/Mac: source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Configuration

All runtime settings are provided via environment variables (an optional `.env` file is supported).

| Variable | Description |
| --- | --- |
| `TELEGRAM_API_ID` | Telegram API ID from https://my.telegram.org |
| `TELEGRAM_API_HASH` | Telegram API hash |
| `TELEGRAM_SESSION_NAME` | Name of the Telethon session file (default `telemedia_user`) |
| `TELEGRAM_GROUP` | Username or numeric ID of the group/channel to monitor |
| `DEFAULT_MESSAGE_LIMIT` | Fallback number of recent messages to inspect (default `30`) |
| `HTTP_TIMEOUT` | HTTP client timeout in seconds (default `12.0`) |
| `REQUEST_CONCURRENCY` | Max concurrent webpage fetches (default `5`) |
| `HTTP_USER_AGENT` | Custom user agent for scraping |
| `ENABLE_SIMILARITY` | Set to `0` to disable TF–IDF similarity matrix |
| `MEDIA_STORAGE_DIR` | Directory for cached media thumbnails (default `media/`) |
| `ENABLE_MEDIA_DOWNLOADS` | Set to `0` to skip downloading original media (keeps thumbnails only) |
| `MEDIA_MAX_BYTES` | Max file size (bytes) eligible for automatic download (default `10485760`) |
| `MEDIA_DOWNLOAD_LIMIT` | Max number of media files downloaded per run (default `6`) |
| `TELEGRAM_GROUP_OPTIONS` | Optional comma-separated list of Telegram groups used as fallback entries for the dashboard dropdown |

Example `.env`:

```
TELEGRAM_API_ID=123456
TELEGRAM_API_HASH=abc123
TELEGRAM_SESSION_NAME=telemedia_user
TELEGRAM_GROUP=@mygroup
DEFAULT_MESSAGE_LIMIT=25
```

## Running the API

```bash
uvicorn telemedia.api:app --reload
```

OpenAPI docs are available at `http://localhost:8000/docs`.

### Web dashboard

Navigate to `http://localhost:8000/` after starting the server to access a lightweight UI. Use the form at the top to change the Telegram group or message limit, and the page will render:

- A pento-style grid of the most recent Telegram messages (with 50px rounded cards) including copy buttons.
- A dropdown that lists the groups/channels your Telegram user account is subscribed to (optionally supplemented by `TELEGRAM_GROUP_OPTIONS` for fallbacks) so operators can switch contexts quickly.
- Inline badges for any detected media/attachments (photos, videos, audio, docs) and URL counts.
- Actual media thumbnails for supported attachments plus quick filters (images/videos/audio/docs) and live search to triage quickly.
- Full-resolution image previews and inline video players, so you can review content without leaving the dashboard.
- Scraped page metadata, keyword trends, and similarity insights without leaving the browser.

### Tests

```bash
python -m unittest discover tests
```

### Authorize the Telegram session (required once)

Before hitting the live Telegram API you must authorize the Telethon user session stored in `.session` files. A helper script is available:

```bash
python scripts/authorize_session.py
```

The script will prompt for your phone number, the SMS/Telegram code, and (if enabled) your two-factor password. Once complete, `telemedia_user.session` will exist and the FastAPI startup hook can connect without failing.

### Main Endpoint

`GET /collect/telegram-group`

Query parameters:

- `group` (optional) – override the configured Telegram group.
- `limit` (optional) – number of recent messages to read (default from config, capped at 200).

Response shape:

```json
{
  "source": "telegram_group",
  "group_id": "@mygroup",
  "collected_at": "2024-05-30T12:00:00Z",
  "messages": [
    {
      "message_id": 42,
      "date": "2024-05-30T11:55:00Z",
      "text": "Flash sale https://example.com",
      "urls": ["https://example.com"],
      "attachments": [
        {
          "media_type": "Photo",
          "file_name": "promo.png",
          "mime_type": "image/png",
          "size_bytes": 2048
        }
      ]
    }
  ],
  "items": [
    {
      "telegram": {"message_id": 10, "text": "...", "date": "...", "urls": ["..."]},
      "page": {
        "url": "https://example.com",
        "title": "Example",
        "description": "Meta description",
        "content_snippet": "Article preview...",
        "analysis": {
          "total_tokens": 123,
          "unique_tokens": 45,
          "top_keywords": [{"word": "sale", "count": 12}]
        }
      }
    }
  ],
  "global_analysis": {
    "similarity_matrix": [[1.0, 0.85], [0.85, 1.0]],
    "most_frequent_keywords": [{"word": "sale", "count": 20}]
  }
}
```

## Architecture Overview

| Module | Responsibility |
| --- | --- |
| `telemedia/config.py` | Loads environment variables (Pydantic settings) and configures logging. |
| `telemedia/telegram_collector.py` | Owns the Telethon client lifecycle and message/URL extraction. |
| `telemedia/web_scraper.py` | Fetches webpages with `httpx` + `BeautifulSoup`, returning normalized page data. |
| `telemedia/analysis.py` | Performs tokenization, keyword frequency, and TF–IDF cosine similarity. |
| `telemedia/schemas.py` | Pydantic models shared between internal layers and the API. |
| `telemedia/api.py` | FastAPI app that orchestrates collectors, scrapers, and analyzers, returning JSON for clients. |

Adding future collectors (search engines, other social networks) now means dropping a new module with the same contract and wiring it into the API router.

## Migrating from the legacy script

- The previous `app/tele_bot.py` synchronous script has been replaced by the `telegram_collector.TelegramCollector` class, which is managed by FastAPI lifecycle hooks.
- Configuration no longer lives in `config/settings.py`; use `.env` or environment variables consumed by `telemedia/config.py`.
- Media processing and Ecwid-specific automation were removed from the default run path. The new API focuses on Telegram scraping + content analytics, but the modular structure leaves room to plug those tasks back in as dedicated services.

## Contributing

1. Fork the repository and create a feature branch.
2. Ensure `uvicorn telemedia.api:app --reload` runs locally and that lint/tests pass.
3. Submit a pull request describing the change and how to test it.

## License

This project remains under the MIT License. See [LICENSE](LICENSE) for details.
