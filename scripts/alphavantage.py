import requests
import json

# ── Configuration ─────────────────────────────────────────────────────────────
API_KEY   = "47ZXJBPGFZ021WCA"
TIME_FROM = "20250101T0000"   # YYYYMMDDTHHMM
TIME_TO   = "20260308T2359"   # YYYYMMDDTHHMM
# ──────────────────────────────────────────────────────────────────────────────

OUTPUT_FILE = "output.json"

params = {
    "function":  "NEWS_SENTIMENT",
    "time_from": TIME_FROM,
    "time_to":   TIME_TO,
    "apikey":    API_KEY,
    "limit":     1000,
}

response = requests.get("https://www.alphavantage.co/query", params=params)
response.raise_for_status()
data = response.json()

# Keep only the fields matching the expected output format
output = {
    "feed": [
        {
            "title":                   article.get("title"),
            "url":                     article.get("url"),
            "published_at":          article.get("time_published"),
            "summary":                 article.get("summary"),
            "source":                  "Alphavantage",
            "topics":                  article.get("topics", []),
            "sentiment_score": article.get("overall_sentiment_score"),
            "ticker_sentiment": [
                {t["ticker"]: float(t["ticker_sentiment_score"])}
                for t in article.get("ticker_sentiment", [])
            ],
        }
        for article in data.get("feed", [])
    ],
}

with open(OUTPUT_FILE, "a") as f:
    json.dump(output, f, indent=4)

print(f"Wrote {len(output['feed'])} articles to {OUTPUT_FILE}")
