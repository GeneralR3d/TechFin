"""AlphaVantage NEWS_SENTIMENT ingestion adapter."""
import hashlib
import logging
from datetime import datetime, timezone

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

AV_URL = "https://www.alphavantage.co/query"


def _make_news_id(url: str, title: str) -> str:
    base = (url or "") + "||" + (title or "")
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def _parse_av_datetime(dt_str: str) -> datetime:
    """Parse AlphaVantage time_published format: '20260307T091122'."""
    try:
        return datetime.strptime(dt_str, "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)


async def fetch_alphavantage_news(
    topics: list[str] | None = None,
    limit: int = 200,
) -> list[dict]:
    """Fetch news from AlphaVantage NEWS_SENTIMENT endpoint.

    Returns empty list if no API key is configured.
    """
    if not settings.ALPHAVANTAGE_API_KEY:
        logger.debug("[alphavantage] No API key configured, skipping")
        return []

    if topics is None:
        topics = ["earnings", "technology"]

    params = {
        "function": "NEWS_SENTIMENT",
        "topics": ",".join(topics),
        "limit": limit,
        "apikey": settings.ALPHAVANTAGE_API_KEY,
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(AV_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        logger.error("[alphavantage] Fetch failed: %s", e)
        return []

    feed = data.get("feed", [])
    rows: list[dict] = []
    seen_ids: set[str] = set()

    for article in feed:
        url = article.get("url", "")
        title = article.get("title", "")
        news_id = _make_news_id(url, title)

        if news_id in seen_ids:
            continue
        seen_ids.add(news_id)

        ticker_sentiment = article.get("ticker_sentiment", [])
        ticker_hint = ticker_sentiment[0]["ticker"] if ticker_sentiment else None

        raw_tags = [t["topic"] for t in article.get("topics", [])]

        rows.append({
            "news_id": news_id,
            "title": title,
            "url": url,
            "summary": article.get("summary", ""),
            "published_at": _parse_av_datetime(article.get("time_published", "")),
            "source": "alphavantage",
            "platform": "alphavantage",
            "ticker_hint": ticker_hint,
            "raw_tags": raw_tags,
        })

    logger.info("[alphavantage] Fetched %s unique articles", len(rows))
    return rows
