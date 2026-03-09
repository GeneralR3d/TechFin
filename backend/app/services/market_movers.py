import logging
import re

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


def _mock_movers() -> dict:
    return {
        "top_gainers": [
            {"ticker": "NVDA", "price": "875.40", "change_amount": "42.30", "change_percentage": "5.08%", "volume": "52,341,200"},
            {"ticker": "META", "price": "512.80", "change_amount": "21.50", "change_percentage": "4.38%", "volume": "18,920,400"},
            {"ticker": "AMD",  "price": "178.65", "change_amount": "6.90",  "change_percentage": "4.02%", "volume": "34,150,800"},
            {"ticker": "TSLA", "price": "248.30", "change_amount": "8.15",  "change_percentage": "3.40%", "volume": "91,230,600"},
            {"ticker": "AMZN", "price": "192.45", "change_amount": "5.60",  "change_percentage": "3.00%", "volume": "29,810,300"},
        ],
        "top_losers": [
            {"ticker": "PFE",  "price": "27.80",  "change_amount": "-1.95", "change_percentage": "-6.56%", "volume": "43,200,100"},
            {"ticker": "INTC", "price": "21.40",  "change_amount": "-1.20", "change_percentage": "-5.31%", "volume": "38,410,700"},
            {"ticker": "BA",   "price": "172.60", "change_amount": "-8.90", "change_percentage": "-4.90%", "volume": "12,650,400"},
            {"ticker": "CVS",  "price": "54.20",  "change_amount": "-2.40", "change_percentage": "-4.24%", "volume": "9,870,200"},
            {"ticker": "WBA",  "price": "10.85",  "change_amount": "-0.45", "change_percentage": "-3.98%", "volume": "15,340,600"},
        ],
        "most_active": [
            {"ticker": "TSLA", "price": "248.30", "change_amount": "8.15",   "change_percentage": "3.40%",  "volume": "91,230,600"},
            {"ticker": "NVDA", "price": "875.40", "change_amount": "42.30",  "change_percentage": "5.08%",  "volume": "52,341,200"},
            {"ticker": "AMD",  "price": "178.65", "change_amount": "6.90",   "change_percentage": "4.02%",  "volume": "34,150,800"},
            {"ticker": "AAPL", "price": "189.50", "change_amount": "-1.20",  "change_percentage": "-0.63%", "volume": "31,540,900"},
            {"ticker": "PFE",  "price": "27.80",  "change_amount": "-1.95",  "change_percentage": "-6.56%", "volume": "43,200,100"},
            {"ticker": "AMZN", "price": "192.45", "change_amount": "5.60",   "change_percentage": "3.00%",  "volume": "29,810,300"},
            {"ticker": "MSFT", "price": "415.20", "change_amount": "3.80",   "change_percentage": "0.92%",  "volume": "22,640,700"},
            {"ticker": "INTC", "price": "21.40",  "change_amount": "-1.20",  "change_percentage": "-5.31%", "volume": "38,410,700"},
            {"ticker": "GOOGL","price": "175.30", "change_amount": "2.10",   "change_percentage": "1.21%",  "volume": "21,130,500"},
            {"ticker": "BAC",  "price": "38.45",  "change_amount": "0.55",   "change_percentage": "1.45%",  "volume": "19,870,300"},
        ],
    }


async def fetch_market_movers() -> dict:
    api_key = settings.ALPHAVANTAGE_API_KEY or "demo"

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://www.alphavantage.co/query",
                params={"function": "TOP_GAINERS_LOSERS", "apikey": api_key},
                timeout=15.0,
            )
            resp.raise_for_status()
            data = resp.json()

        if "Information" in data or "Note" in data:
            logger.warning("[market-movers] API limit reached, using mock data")
            return _mock_movers()

        # US-listed tickers: 1-5 uppercase letters, optional .A/.B share class suffix
        _us_ticker = re.compile(r"^[A-Z]{1,5}(\.[A-Z]{1,2})?$")

        def is_us_ticker(ticker: str) -> bool:
            return bool(_us_ticker.match(ticker))

        def parse_movers_n(items: list, n: int, us_only: bool = False) -> list[dict]:
            result = []
            for item in items:
                if len(result) >= n:
                    break
                ticker = item.get("ticker", "")
                if us_only and not is_us_ticker(ticker):
                    continue
                result.append({
                    "ticker": ticker,
                    "price": item.get("price", "0"),
                    "change_amount": item.get("change_amount", "0"),
                    "change_percentage": item.get("change_percentage", "0%"),
                    "volume": item.get("volume", "0"),
                })
            return result

        gainers = parse_movers_n(data.get("top_gainers", []), 5)
        losers = parse_movers_n(data.get("top_losers", []), 5)
        most_active = parse_movers_n(data.get("most_actively_traded", []), 10, us_only=True)

        if not gainers and not losers and not most_active:
            return _mock_movers()

        return {"top_gainers": gainers, "top_losers": losers, "most_active": most_active}

    except Exception as e:
        logger.error("[market-movers] Fetch error: %s", e)
        return _mock_movers()
