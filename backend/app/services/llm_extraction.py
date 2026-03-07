import json
import logging

from openai import AsyncOpenAI

from app.config import settings
from app.data.yahoo_industries import YAHOO_INDUSTRIES, YAHOO_SECTORS
from app.services.graph_queries import get_existing_context_nodes

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None

SYSTEM_PROMPT = """You are a financial news knowledge graph extractor.
Given a news article or social post, extract structured entities and return ONLY valid JSON.

Rules:
- Industries MUST come from the Yahoo Finance 145-industry taxonomy (e.g. "Biotechnology", "Oil & Gas Integrated", "Semiconductors")
- Sectors MUST be one of: Technology, Healthcare, Financial Services, Consumer Cyclical, Consumer Defensive, Energy, Industrials, Basic Materials, Real Estate, Utilities, Communication Services
- MacroTheme is a high-level narrative (e.g. "US Rate Hikes 2022-2024", "AI Chip Boom", "Banking Crisis 2023", "China Slowdown")
- Event is a specific dated occurrence (e.g. "Fed raises rates 25bps - May 2023", "SVB Bank Collapse", "Apple Q1 2025 Earnings")
- sentiment_score: float from -1.0 (very bearish) to 1.0 (very bullish), 0.0 = neutral

Return JSON matching this exact schema:
{
  "macro_themes": [{"name": "string", "description": "string (1 sentence)"}],
  "events": [{"title": "string", "type": "earnings|merger|ipo|regulation|rate_decision|economic_data|product_launch|geopolitical|other", "date": "YYYY-MM-DD or null", "description": "string (1 sentence)"}],
  "companies": [{"ticker": "string or null", "name": "string"}],
  "sectors": ["string"],
  "industries": ["string"],
  "indicators": [{"name": "string", "type": "interest_rate|inflation|gdp|employment|market_index|commodity|currency|other"}],
  "geographies": [{"name": "string", "geo_type": "country|region|city"}],
  "institutions": [{"name": "string", "inst_type": "central_bank|regulator|exchange|fund|bank|other"}],
  "persons": [{"name": "string", "role": "string or null"}],
  "sentiment_score": 0.0,
  "summary": "string (max 30 words)"
}

If a field has no matches, return an empty array. For sentiment_score, return 0.0 if neutral."""


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


def _empty_extraction() -> dict:
    return {
        "macro_themes": [],
        "events": [],
        "companies": [],
        "sectors": [],
        "industries": [],
        "indicators": [],
        "geographies": [],
        "institutions": [],
        "persons": [],
        "sentiment_score": 0.0,
        "summary": "",
    }


async def extract_entities(title: str, content: str) -> dict:
    """Call OpenAI to extract graph entities from a news article/post."""
    if not settings.OPENAI_API_KEY:
        logger.debug("[llm] No OpenAI key configured — skipping extraction")
        return _empty_extraction()

    user_prompt = f"Title: {title}\nContent: {content}"

    context_nodes = await get_existing_context_nodes()
    macro_themes = context_nodes["macro_themes"]
    events = context_nodes["events"]

    if macro_themes or events:
        context_lines = ["EXISTING GRAPH DB NODES (reuse these strings exactly if applicable):"]
        if macro_themes:
            context_lines.append(f"MacroThemes: {', '.join(macro_themes)}")
        if events:
            context_lines.append(f"Events: {', '.join(events)}")
        system_prompt = "\n".join(context_lines) + "\n\n" + SYSTEM_PROMPT
        logger.info("[llm] Context: %d themes, %d events injected into prompt", len(macro_themes), len(events))
    else:
        system_prompt = SYSTEM_PROMPT

    try:
        client = _get_client()
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            timeout=30.0,
        )
        raw = response.choices[0].message.content or "{}"
        data = json.loads(raw)

        # Validate sectors/industries against canonical lists
        data["sectors"] = [s for s in data.get("sectors", []) if s in YAHOO_SECTORS]
        data["industries"] = [i for i in data.get("industries", []) if i in YAHOO_INDUSTRIES]

        return data

    except Exception as e:
        logger.error("[llm] Extraction failed: %s", e)
        return _empty_extraction()
