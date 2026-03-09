import asyncio
import logging

import httpx

logger = logging.getLogger(__name__)

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


def _mock_sectors() -> list[dict]:
    mock_returns = [1.85, 0.42, -0.31, 2.10, -1.20, 0.75, -0.55, 3.20, 0.15, -0.80, 0.60]
    mock_ytd = [8.45, 4.20, -1.50, 12.30, -3.10, 5.60, 2.10, 18.40, 1.80, -2.30, 3.70]
    mock_prices = [215.30, 42.15, 138.90, 190.45, 74.20, 118.60, 72.40, 94.15, 88.20, 65.30, 42.80]
    return [
        {
            "symbol": s["symbol"],
            "name": s["name"],
            "day_return": mock_returns[i],
            "ytd_return": mock_ytd[i],
            "market_weight": s["market_weight"],
            "price": mock_prices[i],
        }
        for i, s in enumerate(SECTOR_MAP)
    ]


async def _fetch_single_sector(client: httpx.AsyncClient, sector: dict) -> dict:
    symbol = sector["symbol"]
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    try:
        resp = await client.get(
            url,
            params={"interval": "1d", "range": "ytd"},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10.0,
        )
        resp.raise_for_status()
        data = resp.json()
        meta = data["chart"]["result"][0]["meta"]

        current_price = meta.get("regularMarketPrice", 0.0)
        prev_close = meta.get("chartPreviousClose") or meta.get("previousClose", current_price)
        day_return = ((current_price - prev_close) / prev_close * 100) if prev_close else 0.0

        closes = data["chart"]["result"][0].get("indicators", {}).get("quote", [{}])[0].get("close", [])
        valid_closes = [c for c in closes if c is not None]
        if len(valid_closes) >= 2:
            ytd_return = (valid_closes[-1] - valid_closes[0]) / valid_closes[0] * 100
        else:
            ytd_return = 0.0

        return {
            "symbol": symbol,
            "name": sector["name"],
            "day_return": round(day_return, 2),
            "ytd_return": round(ytd_return, 2),
            "market_weight": sector["market_weight"],
            "price": round(current_price, 2),
        }
    except Exception as e:
        logger.warning("[sectors] Failed to fetch %s: %s", symbol, e)
        return None  # type: ignore[return-value]


async def fetch_sector_data() -> list[dict]:
    try:
        async with httpx.AsyncClient() as client:
            results = await asyncio.gather(
                *[_fetch_single_sector(client, s) for s in SECTOR_MAP],
                return_exceptions=True,
            )

        sectors = []
        mock = _mock_sectors()
        for i, result in enumerate(results):
            if isinstance(result, dict) and result is not None:
                sectors.append(result)
            else:
                logger.warning("[sectors] Using mock for %s", SECTOR_MAP[i]["symbol"])
                sectors.append(mock[i])
        return sectors

    except Exception as e:
        logger.error("[sectors] Fetch error: %s", e)
        return _mock_sectors()
