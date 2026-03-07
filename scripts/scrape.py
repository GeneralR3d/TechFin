# yahoo RSS news
import time
import json
import hashlib #cryptographic hashing
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime # format email header?
from pathlib import Path #make code more readble, trade file path as objects rather than strings
from urllib.parse import quote_plus #break down or build url

import feedparser #third party library
import pandas as pd

OUTPUT_DIR = Path("data/news")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CSV_PATH = OUTPUT_DIR / "yahoo_finance_rss_news.csv"
JSON_PATH = OUTPUT_DIR / "yahoo_finance_rss_news.json"

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

# Yahoo ticker RSS pattern
# Example seen publicly:
# https://feeds.finance.yahoo.com/rss/2.0/headline?lang=en-US&region=US&s=AAPL
TICKER_FEED_TEMPLATE = (
    "https://feeds.finance.yahoo.com/rss/2.0/headline"
    "?lang=en-US&region=US&s={ticker}"
)

REQUEST_PAUSE_SECONDS = 0.5



# macro topics
def detect_theme(text: str) -> str:
    t = (text or "").lower()

    if any(k in t for k in ["banking crisis", "svb", "silicon valley bank", "regional bank", "bank run"]):
        return "2023_banking_crisis"

    if any(k in t for k in ["rate cut", "fed cut", "fomc", "federal reserve", "interest rate"]):
        return "2024_rate_cuts"

    if any(k in t for k in ["inflation", "cpi", "pce"]):
        return "inflation"

    if any(k in t for k in ["recession", "slowdown", "soft landing"]):
        return "growth_outlook"

    return "other"


#continue


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


def parse_single_feed(feed_url: str, source_label: str):
    parsed = feedparser.parse(feed_url)

    if getattr(parsed, "bozo", 0):
        print(f"[WARN] Feed parse issue for {feed_url}: {getattr(parsed, 'bozo_exception', None)}")

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

        # Some feeds include category/tags
        tags = []
        if "tags" in entry:
            for tag in entry.tags:
                term = getattr(tag, "term", None)
                if term:
                    tags.append(term)

        row = {
            "news_id": make_news_id(link, title),
            "source": "Yahoo Finance RSS",
            "source_feed": source_label,
            "feed_url": feed_url,
            "title": title,
            "link": link,
            "summary": summary,
            "published_raw": published_raw,
            "published_utc": published_utc,
            "tags": tags,
            "fetched_utc": datetime.now(timezone.utc).isoformat(),
        }
        rows.append(row)

    return rows


def extract_ticker_from_url(feed_url: str):
    marker = "&s="
    if marker in feed_url:
        return feed_url.split(marker, 1)[1]
    return None


def enrich_rows_with_ticker(rows):
    enriched = []
    for row in rows:
        ticker = None
        if "headline" in row["feed_url"] and "&s=" in row["feed_url"]:
            ticker = extract_ticker_from_url(row["feed_url"])
        row["ticker_hint"] = ticker
        enriched.append(row)
    return enriched


def deduplicate_rows(rows):
    seen_ids = set()
    seen_links = set()
    deduped = []

    for row in rows:
        news_id = row["news_id"]
        link = row["link"]

        # Prefer URL dedupe first, then hash fallback
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
        df = pd.read_csv(csv_path)
        return df
    except Exception as e:
        print(f"[WARN] Could not read existing CSV: {e}")
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

    # Normalize missing columns if schema evolved
    for col in [
        "news_id", "source", "source_feed", "feed_url", "title", "link",
        "summary", "published_raw", "published_utc", "tags", "fetched_utc", "ticker_hint"
    ]:
        if col not in combined.columns:
            combined[col] = None

    combined = combined.drop_duplicates(subset=["link"], keep="first")
    combined = combined.drop_duplicates(subset=["news_id"], keep="first")

    # Sort by published time descending when possible
    if "published_utc" in combined.columns:
        combined["published_utc_sort"] = pd.to_datetime(
            combined["published_utc"], errors="coerce", utc=True
        )
        combined = combined.sort_values("published_utc_sort", ascending=False)
        combined = combined.drop(columns=["published_utc_sort"])

    return combined.reset_index(drop=True)


# =========================
# MAIN
# =========================

def main():
    all_feed_urls = []
    all_feed_urls.extend([(url, "general") for url in GENERAL_FEEDS])
    all_feed_urls.extend(
        [(url, "ticker") for url in build_ticker_feed_urls(TICKERS)]
    )

    all_rows = []

    print(f"[INFO] Total feeds to ingest: {len(all_feed_urls)}")

    for i, (feed_url, source_label) in enumerate(all_feed_urls, start=1):
        print(f"[INFO] ({i}/{len(all_feed_urls)}) Fetching: {feed_url}")
        rows = parse_single_feed(feed_url, source_label)
        rows = enrich_rows_with_ticker(rows)
        all_rows.extend(rows)
        time.sleep(REQUEST_PAUSE_SECONDS)

    print(f"[INFO] Raw rows collected: {len(all_rows)}")

    deduped_rows = deduplicate_rows(all_rows)
    print(f"[INFO] Deduped rows this run: {len(deduped_rows)}")

    combined_df = merge_with_existing(deduped_rows, CSV_PATH)

    if combined_df.empty:
        print("[INFO] No news found.")
        return

    combined_df.to_csv(CSV_PATH, index=False)

    records = combined_df.to_dict(orient="records")
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    print(f"[INFO] Saved CSV:  {CSV_PATH}")
    print(f"[INFO] Saved JSON: {JSON_PATH}")
    print(f"[INFO] Total stored rows: {len(combined_df)}")


if __name__ == "__main__":
    main()


