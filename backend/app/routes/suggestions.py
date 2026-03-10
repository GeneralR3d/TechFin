"""AI-powered portfolio suggestions: hold/sell recommendations based on recent news."""
import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models.holding import Holding
from app.models.user import User
from app.services import graph_queries, llm_analysis
from app.services.yahoo_finance import fetch_yahoo_finance_news

router = APIRouter(prefix="/api/suggestions", tags=["suggestions"])
logger = logging.getLogger(__name__)


class TickerSuggestion(BaseModel):
    ticker: str
    quantity: float
    action: str  # "HOLD" | "SELL"
    confidence: str  # "high" | "medium" | "low"
    short_term_pct: float | None = None
    short_term_label: str | None = None
    long_term_pct: float | None = None
    long_term_label: str | None = None
    price_outlook: str
    reasoning: str


class PortfolioSuggestionsResponse(BaseModel):
    suggestions: list[TickerSuggestion]
    market_context: str | None = None


@router.get("", response_model=PortfolioSuggestionsResponse)
async def get_suggestions(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # 1. Fetch user's holdings
    result = await db.execute(
        select(Holding).where(Holding.user_id == user.id).order_by(Holding.created_at)
    )
    holdings = result.scalars().all()

    if not holdings:
        return PortfolioSuggestionsResponse(
            suggestions=[],
            market_context=None,
        )

    holdings_data = [{"ticker": h.ticker, "quantity": float(h.quantity)} for h in holdings]
    tickers = [h.ticker for h in holdings]

    # 2. Fetch news per ticker from Neo4j graph (in parallel)
    async def safe_fetch(ticker: str) -> tuple[str, list[dict]]:
        try:
            articles = await graph_queries.get_articles_by_company(ticker, limit=8)
            return ticker, articles
        except Exception as e:
            logger.warning("[suggestions] Graph fetch failed for %s: %s", ticker, e)
            return ticker, []

    ticker_results = await asyncio.gather(*[safe_fetch(t) for t in tickers])
    articles_by_ticker: dict[str, list[dict]] = dict(ticker_results)

    # 3. Fetch recent general market news for broader context
    try:
        market_articles_raw = await fetch_yahoo_finance_news()
        # Normalize to graph article format (use summary as summary)
        recent_market_articles = [
            {
                "news_id": a.get("id", ""),
                "title": a.get("title", ""),
                "url": a.get("url", ""),
                "summary": a.get("summary", ""),
            }
            for a in market_articles_raw[:10]
        ]
    except Exception as e:
        logger.warning("[suggestions] Failed to fetch market news: %s", e)
        recent_market_articles = []

    # 4. Call LLM for suggestions
    llm_result = await llm_analysis.generate_portfolio_suggestions(
        holdings=holdings_data,
        articles_by_ticker=articles_by_ticker,
        recent_market_articles=recent_market_articles,
    )

    if not llm_result:
        # Fallback: return neutral HOLD for each ticker with no AI reasoning
        fallback = [
            TickerSuggestion(
                ticker=h["ticker"],
                quantity=h["quantity"],
                action="HOLD",
                confidence="low",
                short_term_pct=None,
                short_term_label=None,
                long_term_pct=None,
                long_term_label=None,
                price_outlook="Unable to generate AI analysis at this time.",
                reasoning="No OpenAI API key configured or analysis unavailable.",
            )
            for h in holdings_data
        ]
        return PortfolioSuggestionsResponse(suggestions=fallback, market_context=None)

    # 5. Merge LLM suggestions with quantity from holdings
    quantity_map = {h["ticker"]: h["quantity"] for h in holdings_data}
    llm_suggestions = llm_result.get("suggestions", [])
    merged: list[TickerSuggestion] = []

    for s in llm_suggestions:
        ticker = s.get("ticker", "").upper()
        merged.append(
            TickerSuggestion(
                ticker=ticker,
                quantity=quantity_map.get(ticker, 0),
                action=s.get("action", "HOLD").upper(),
                confidence=s.get("confidence", "medium").lower(),
                short_term_pct=float(s["short_term_pct"]) if s.get("short_term_pct") is not None else None,
                short_term_label=s.get("short_term_label"),
                long_term_pct=float(s["long_term_pct"]) if s.get("long_term_pct") is not None else None,
                long_term_label=s.get("long_term_label"),
                price_outlook=s.get("price_outlook", ""),
                reasoning=s.get("reasoning", ""),
            )
        )

    # Any ticker missing from LLM output gets a neutral entry
    covered = {s.ticker for s in merged}
    for h in holdings_data:
        if h["ticker"] not in covered:
            merged.append(
                TickerSuggestion(
                    ticker=h["ticker"],
                    quantity=h["quantity"],
                    action="HOLD",
                    confidence="low",
                    short_term_pct=None,
                    short_term_label=None,
                    long_term_pct=None,
                    long_term_label=None,
                    price_outlook="Insufficient data to generate a prediction.",
                    reasoning="No recent news found for this ticker.",
                )
            )

    return PortfolioSuggestionsResponse(
        suggestions=merged,
        market_context=llm_result.get("market_context"),
    )
