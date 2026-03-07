"""RSS ingestion adapter — ported from scripts/hourlyyahoo.py for use inside the app."""
import hashlib
import logging
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import quote_plus

import feedparser

logger = logging.getLogger(__name__)

GENERAL_FEEDS = [
    "https://finance.yahoo.com/rss/topstories",
    "https://finance.yahoo.com/rss/market",
    "https://finance.yahoo.com/rss/industry",
]

TICKERS = [
    "JPM", "BAC", "C", "GS", "MS", "WFC",
    "KRE", "SCHW", "AXP",
    "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META",
    "SPY", "QQQ", "IWM", "TLT",
    "XOM", "CVX",
    "AMD", "AVGO", "TSM",
]

TICKER_FEED_TEMPLATE = (
    "https://feeds.finance.yahoo.com/rss/2.0/headline"
    "?lang=en-US&region=US&s={ticker}"
)

REQUEST_PAUSE_SECONDS = 0.5


def _make_news_id(link: str, title: str) -> str:
    base = (link or "") + "||" + (title or "")
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def _safe_parse_datetime(dt_str: str) -> datetime | None:
    if not dt_str:
        return None
    try:
        dt = parsedate_to_datetime(dt_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _extract_ticker_from_url(feed_url: str) -> str | None:
    marker = "&s="
    if marker in feed_url:
        return feed_url.split(marker, 1)[1]
    return None


def _parse_single_feed(feed_url: str, source_label: str) -> list[dict]:
    parsed = feedparser.parse(feed_url)
    rows = []

    for entry in parsed.entries:
        title = entry.get("title", "").strip()
        link = entry.get("link", "").strip()
        summary = entry.get("summary", "").strip()

        published_raw = (
            entry.get("published")
            or entry.get("updated")
            or entry.get("pubDate")
            or ""
        )
        published_dt = _safe_parse_datetime(published_raw)

        tags = []
        if "tags" in entry:
            for tag in entry.tags:
                term = getattr(tag, "term", None)
                if term:
                    tags.append(term)

        rows.append({
            "news_id": _make_news_id(link, title),
            "title": title,
            "url": link,
            "summary": summary,
            "published_at": published_dt or datetime.now(timezone.utc),
            "source": "yahoo_rss",
            "platform": "yahoo_finance",
            "ticker_hint": (
                _extract_ticker_from_url(feed_url) if source_label == "ticker" else None
            ),
            "raw_tags": tags,
        })

    return rows


def fetch_yahoo_rss() -> list[dict]:
    """Fetch all Yahoo Finance RSS feeds and return deduplicated article dicts."""
    all_feed_urls = []
    all_feed_urls.extend([(url, "general") for url in GENERAL_FEEDS])

    for ticker in TICKERS:
        ticker = ticker.strip().upper()
        url = TICKER_FEED_TEMPLATE.format(ticker=quote_plus(ticker))
        all_feed_urls.append((url, "ticker"))

    all_rows: list[dict] = []
    seen_ids: set[str] = set()
    seen_links: set[str] = set()

    for i, (feed_url, source_label) in enumerate(all_feed_urls, start=1):
        logger.info("[news_fetcher] Fetching %s/%s: %s", i, len(all_feed_urls), feed_url)
        try:
            rows = _parse_single_feed(feed_url, source_label)
            for row in rows:
                nid = row["news_id"]
                link = row["url"]
                if link and link in seen_links:
                    continue
                if nid in seen_ids:
                    continue
                all_rows.append(row)
                seen_ids.add(nid)
                if link:
                    seen_links.add(link)
        except Exception as e:
            logger.warning("[news_fetcher] Failed to parse %s: %s", feed_url, e)

        time.sleep(REQUEST_PAUSE_SECONDS)

    logger.info("[news_fetcher] Fetched %s unique articles", len(all_rows))
    return all_rows
