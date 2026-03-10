from pydantic import BaseModel


class TickerResponse(BaseModel):
    symbol: str
    name: str
    sector: str | None = None


class TickerSuggestion(BaseModel):
    ticker: str
    quantity: float
    action: str  # "HOLD" | "SELL"
    confidence: str  # "high" | "medium" | "low"
    price_outlook: str
    reasoning: str


class PortfolioSuggestionsResponse(BaseModel):
    suggestions: list["TickerSuggestion"]
    market_context: str | None = None
