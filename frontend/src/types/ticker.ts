export interface Ticker {
  symbol: string;
  name: string;
  sector?: string;
}

export interface TickerSuggestion {
  ticker: string;
  quantity: number;
  action: "HOLD" | "SELL";
  confidence: "high" | "medium" | "low";
  short_term_pct: number | null;
  short_term_label: string | null;
  long_term_pct: number | null;
  long_term_label: string | null;
  price_outlook: string;
  reasoning: string;
}

export interface PortfolioSuggestionsResponse {
  suggestions: TickerSuggestion[];
  market_context: string | null;
}
