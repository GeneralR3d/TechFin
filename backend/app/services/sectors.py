import asyncio
import logging
import time

import httpx

logger = logging.getLogger(__name__)

# ETF symbol + market weight
SECTOR_MAP = [
    {"symbol": "XLK",  "name": "Technology",          "market_weight": 29.0},
    {"symbol": "XLF",  "name": "Financials",           "market_weight": 13.0},
    {"symbol": "XLV",  "name": "Healthcare",           "market_weight": 12.0},
    {"symbol": "XLY",  "name": "Consumer Cyclical",    "market_weight": 10.0},
    {"symbol": "XLC",  "name": "Comm. Services",       "market_weight": 8.0},
    {"symbol": "XLI",  "name": "Industrials",          "market_weight": 8.0},
    {"symbol": "XLP",  "name": "Consumer Defensive",   "market_weight": 6.0},
    {"symbol": "XLE",  "name": "Energy",               "market_weight": 4.0},
    {"symbol": "XLB",  "name": "Materials",            "market_weight": 2.5},
    {"symbol": "XLU",  "name": "Utilities",            "market_weight": 2.5},
    {"symbol": "XLRE", "name": "Real Estate",          "market_weight": 2.5},
]

_cache: dict = {"data": None, "ts": 0.0}
_CACHE_TTL = 15 * 60  # 15 minutes


async def _fetch_etf_data(client: httpx.AsyncClient, symbol: str) -> dict:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    try:
        resp = await client.get(
            url,
            params={"interval": "1d", "range": "5d"},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10.0,
        )
        resp.raise_for_status()
        result = resp.json()["chart"]["result"][0]
        meta = result["meta"]
        price = round(meta.get("regularMarketPrice", 0.0), 2)
        ytd_base = meta.get("chartPreviousClose", 0.0)  # Dec 31 prev year

        # Get yesterday's close from the closes array (last non-null value)
        closes = result.get("indicators", {}).get("quote", [{}])[0].get("close", [])
        valid_closes = [c for c in closes if c is not None]
        week_base = valid_closes[0] if valid_closes else 0.0

        week_return = round((price - week_base) / week_base * 100, 2) if week_base else 0.0
        ytd_return = round((price - ytd_base) / ytd_base * 100, 2) if ytd_base else 0.0

        return {"price": price, "week_return": week_return, "ytd_return": ytd_return}
    except Exception as e:
        logger.debug("[sectors] ETF data fetch failed for %s: %s", symbol, e)
        return {"price": 0.0, "day_return": 0.0, "ytd_return": 0.0}


async def fetch_sector_data() -> list[dict]:
    now = time.monotonic()
    if _cache["data"] and now - _cache["ts"] < _CACHE_TTL:
        return _cache["data"]

    symbols = [s["symbol"] for s in SECTOR_MAP]
    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(
            *[_fetch_etf_data(client, sym) for sym in symbols],
            return_exceptions=True,
        )

    sectors = []
    for entry, result in zip(SECTOR_MAP, results):
        data = result if isinstance(result, dict) else {"price": 0.0, "day_return": 0.0, "ytd_return": 0.0}
        sectors.append({
            "symbol": entry["symbol"],
            "name": entry["name"],
            "week_return": data["week_return"],
            "ytd_return": data["ytd_return"],
            "market_weight": entry["market_weight"],
            "price": data["price"],
        })

    _cache["data"] = sectors
    _cache["ts"] = now
    return sectors
