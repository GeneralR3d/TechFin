import time
import json
import hashlib
import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import quote_plus

import feedparser
import pandas as pd
from apscheduler.schedulers.blocking import BlockingScheduler

OUTPUT_DIR = Path("data/news")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CSV_PATH = OUTPUT_DIR / "yahoo_finance_rss_news_update.csv"
JSON_PATH = OUTPUT_DIR / "yahoo_finance_rss_news_update.json"
LOG_PATH = OUTPUT_DIR / "ingest.log"

GENERAL_FEEDS = [
    "https://finance.yahoo.com/rss/topstories",
    "https://finance.yahoo.com/rss/market",
    "https://finance.yahoo.com/rss/industry",
]

TICKERS = [
    # Banks
    "JPM", "BAC", "C", "GS", "MS", "WFC",
    # Regional banks / financials
    "KRE", "SCHW", "AXP",
    # Big tech
    "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META",
    # Market / macro
    "SPY", "QQQ", "IWM", "TLT",
    # Energy
    "XOM", "CVX", 
    # Semis / cyclicals??
    "AMD", "AVGO", "TSM"
]


TICKER_FEED_TEMPLATE = (
    "https://feeds.finance.yahoo.com/rss/2.0/headline"
    "?lang=en-US&region=US&s={ticker}"
)

REQUEST_PAUSE_SECONDS = 0.5


# logging
logger = logging.getLogger("yahoo_rss_ingest")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = TimedRotatingFileHandler(
        LOG_PATH,
        when="h",
        interval=1,
        backupCount=48,
        encoding="utf-8"
    )
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# help


def safe_parse_datetime(dt_str: str):
    if not dt_str:
        return None
    try:
        dt = parsedate_to_datetime(dt_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def make_news_id(link: str, title: str) -> str:
    base = (link or "") + "||" + (title or "")
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def build_ticker_feed_urls(tickers):
    urls = []
    for ticker in tickers:
        ticker = ticker.strip().upper()
        if ticker:
            urls.append(TICKER_FEED_TEMPLATE.format(ticker=quote_plus(ticker)))
    return urls


def extract_ticker_from_url(feed_url: str):
    marker = "&s="
    if marker in feed_url:
        return feed_url.split(marker, 1)[1]
    return None


def parse_single_feed(feed_url: str, source_label: str):
    parsed = feedparser.parse(feed_url)

    if getattr(parsed, "bozo", 0):
        logger.warning("Feed parse issue for %s: %s", feed_url, getattr(parsed, "bozo_exception", None))

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
        published_dt = safe_parse_datetime(published_raw)
        published_utc = published_dt.isoformat() if published_dt else None

        tags = []
        if "tags" in entry:
            for tag in entry.tags:
                term = getattr(tag, "term", None)
                if term:
                    tags.append(term)

        rows.append({
            "news_id": make_news_id(link, title),
            "source": "Yahoo Finance RSS",
            "source_feed": source_label,
            "feed_url": feed_url,
            "ticker_hint": extract_ticker_from_url(feed_url) if source_label == "ticker" else None,
            "title": title,
            "link": link,
            "summary": summary,
            "published_raw": published_raw,
            "published_utc": published_utc,
            "tags": json.dumps(tags, ensure_ascii=False),
            "fetched_utc": datetime.now(timezone.utc).isoformat(),
        })

    return rows


def deduplicate_rows(rows):
    seen_ids = set()
    seen_links = set()
    deduped = []

    for row in rows:
        news_id = row["news_id"]
        link = row["link"]

        if link and link in seen_links:
            continue
        if news_id in seen_ids:
            continue

        deduped.append(row)
        seen_ids.add(news_id)
        if link:
            seen_links.add(link)

    return deduped


def load_existing_csv(csv_path: Path):
    if not csv_path.exists():
        return pd.DataFrame()

    try:
        return pd.read_csv(csv_path)
    except Exception as e:
        logger.warning("Could not read existing CSV: %s", e)
        return pd.DataFrame()


def merge_with_existing(new_rows, csv_path: Path):
    new_df = pd.DataFrame(new_rows)

    if new_df.empty:
        return new_df

    old_df = load_existing_csv(csv_path)

    if old_df.empty:
        combined = new_df.copy()
    else:
        combined = pd.concat([old_df, new_df], ignore_index=True)

    for col in [
        "news_id", "source", "source_feed", "feed_url", "ticker_hint",
        "title", "link", "summary", "published_raw", "published_utc",
        "tags", "fetched_utc"
    ]:
        if col not in combined.columns:
            combined[col] = None

    combined = combined.drop_duplicates(subset=["link"], keep="first")
    combined = combined.drop_duplicates(subset=["news_id"], keep="first")

    combined["published_utc_sort"] = pd.to_datetime(
        combined["published_utc"], errors="coerce", utc=True
    )
    combined = combined.sort_values("published_utc_sort", ascending=False)
    combined = combined.drop(columns=["published_utc_sort"])

    return combined.reset_index(drop=True)


def ingest_once():
    logger.info("Starting hourly Yahoo Finance RSS ingestion")

    all_feed_urls = []
    all_feed_urls.extend([(url, "general") for url in GENERAL_FEEDS])
    all_feed_urls.extend([(url, "ticker") for url in build_ticker_feed_urls(TICKERS)])

    all_rows = []

    for i, (feed_url, source_label) in enumerate(all_feed_urls, start=1):
        logger.info("Fetching %s/%s: %s", i, len(all_feed_urls), feed_url)
        rows = parse_single_feed(feed_url, source_label)
        all_rows.extend(rows)
        time.sleep(REQUEST_PAUSE_SECONDS)

    logger.info("Raw rows collected this run: %s", len(all_rows))

    deduped_rows = deduplicate_rows(all_rows)
    logger.info("Deduped rows this run: %s", len(deduped_rows))

    combined_df = merge_with_existing(deduped_rows, CSV_PATH)

    if combined_df.empty:
        logger.info("No rows to save")
        return

    combined_df.to_csv(CSV_PATH, index=False)

    records = combined_df.to_dict(orient="records")
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    logger.info("Saved CSV to %s", CSV_PATH)
    logger.info("Saved JSON to %s", JSON_PATH)
    logger.info("Total stored rows: %s", len(combined_df))


if __name__ == "__main__":
    scheduler = BlockingScheduler(timezone="Asia/Singapore")

    # Run once immediately when script starts
    ingest_once()

    # Then run every hour on the hour
    scheduler.add_job(
    ingest_once,
    trigger="interval",
    hours=1
    )

    logger.info("Scheduler started: runs every hour at minute 0")
    scheduler.start()
