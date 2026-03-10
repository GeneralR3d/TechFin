import logging
import re
import time

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_cache: dict = {"data": None, "ts": 0.0}
_CACHE_TTL = 5 * 60  # 5 minutes

_us_ticker = re.compile(r"^[A-Z]{1,5}(\.[A-Z]{1,2})?$")


def _is_us_ticker(ticker: str) -> bool:
    return bool(_us_ticker.match(ticker))


def _parse_movers(items: list, n: int, us_only: bool = False) -> list[dict]:
    result = []
    for item in items:
        if len(result) >= n:
            break
        ticker = item.get("ticker", "")
        if us_only and not _is_us_ticker(ticker):
            continue
        result.append({
            "ticker": ticker,
            "price": item.get("price", "0"),
            "change_amount": item.get("change_amount", "0"),
            "change_percentage": item.get("change_percentage", "0%"),
            "volume": item.get("volume", "0"),
        })
    return result


async def _fetch_alphavantage_movers(api_key: str) -> dict | None:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://www.alphavantage.co/query",
            params={"function": "TOP_GAINERS_LOSERS", "apikey": api_key},
            timeout=15.0,
        )
        resp.raise_for_status()
        data = resp.json()

    if "Information" in data or "Note" in data:
        logger.warning("[market-movers] AlphaVantage rate limited")
        return None

    gainers = _parse_movers(data.get("top_gainers", []), 5)
    losers = _parse_movers(data.get("top_losers", []), 5)
    most_active = _parse_movers(data.get("most_actively_traded", []), 10, us_only=True)

    if not gainers and not losers and not most_active:
        return None

    return {"top_gainers": gainers, "top_losers": losers, "most_active": most_active}


def _parse_yahoo_quote(item: dict) -> dict:
    ticker = item.get("symbol", "")
    price = item.get("regularMarketPrice", 0.0)
    change = item.get("regularMarketChange", 0.0)
    pct = item.get("regularMarketChangePercent", 0.0)
    volume = item.get("regularMarketVolume", 0)
    return {
        "ticker": ticker,
        "price": f"{price:.2f}",
        "change_amount": f"{change:+.2f}",
        "change_percentage": f"{pct:+.2f}%",
        "volume": f"{volume:,}",
    }


async def _fetch_yahoo_movers() -> dict | None:
    base = "https://query1.finance.yahoo.com/v1/finance/screener/predefined/saved"
    params_list = [
        ("day_gainers", "top_gainers", 5),
        ("day_losers", "top_losers", 5),
        ("most_actives", "most_active", 10),
    ]
    result: dict = {}
    async with httpx.AsyncClient() as client:
        for scr_id, key, n in params_list:
            try:
                resp = await client.get(
                    base,
                    params={"scrIds": scr_id, "count": n},
                    headers={"User-Agent": "Mozilla/5.0"},
                    timeout=10.0,
                )
                resp.raise_for_status()
                data = resp.json()
                quotes = (
                    data.get("finance", {})
                    .get("result", [{}])[0]
                    .get("quotes", [])
                )
                result[key] = [_parse_yahoo_quote(q) for q in quotes[:n]]
            except Exception as e:
                logger.debug("[market-movers] Yahoo %s failed: %s", scr_id, e)
                result[key] = []

    if not any(result.values()):
        return None
    return result


async def fetch_market_movers() -> dict:
    now = time.monotonic()
    if _cache["data"] and now - _cache["ts"] < _CACHE_TTL:
        return _cache["data"]

    api_key = settings.ALPHAVANTAGE_API_KEY or "demo"

    # Primary: AlphaVantage
    try:
        data = await _fetch_alphavantage_movers(api_key)
        if data:
            _cache["data"] = data
            _cache["ts"] = now
            return data
    except Exception as e:
        logger.warning("[market-movers] AlphaVantage failed: %s", e)

    # Secondary: Yahoo Finance
    try:
        data = await _fetch_yahoo_movers()
        if data:
            _cache["data"] = data
            _cache["ts"] = now
            return data
    except Exception as e:
        logger.warning("[market-movers] Yahoo movers failed: %s", e)

    # Both failed — return empty (no stale mock)
    logger.error("[market-movers] All sources failed, returning empty lists")
    return {"top_gainers": [], "top_losers": [], "most_active": []}
