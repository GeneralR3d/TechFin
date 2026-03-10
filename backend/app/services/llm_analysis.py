"""LLM-powered analysis for events and macro themes, with in-memory TTL cache."""
import json
import logging
import time

from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)

_TTL_SECONDS = 3600  # 1 hour
_cache: dict[str, tuple[dict, float]] = {}

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


def _cache_get(key: str) -> dict | None:
    entry = _cache.get(key)
    if entry is None:
        return None
    value, ts = entry
    if time.monotonic() - ts > _TTL_SECONDS:
        del _cache[key]
        return None
    return value


def _cache_set(key: str, value: dict) -> None:
    _cache[key] = (value, time.monotonic())


_ANALYSIS_SCHEMA = """{
  "executive_summary": "string",
  "key_risks": ["string", ...],
  "potential_developments": ["string", ...],
  "relevant_parties": [{"name": "string", "role": "string", "significance": "string"}],
  "market_impact": "string",
  "citations": [{"news_id": "string", "title": "string", "url": "string"}]
}"""

_SYSTEM_PROMPT = (
    "You are a financial analyst. Analyze the given macro {subject_type} based on recent news articles. "
    "Return ONLY valid JSON matching this exact schema:\n" + _ANALYSIS_SCHEMA + "\n"
    "Keep executive_summary under 100 words. Provide 2-4 key_risks and 2-4 potential_developments. "
    "List up to 5 relevant_parties. Citations must reference news_ids from the provided articles."
)


def _build_articles_text(articles: list[dict], max_articles: int = 10) -> str:
    lines = []
    for a in articles[:max_articles]:
        news_id = a.get("news_id", "")
        title = a.get("title", "")
        summary = a.get("summary", "") or ""
        url = a.get("url", "")
        lines.append(f"[{news_id}] {title}\nURL: {url}\nSummary: {summary[:300]}")
    return "\n\n".join(lines)


def _build_entities_text(entities: dict) -> str:
    parts = []
    companies = [c.get("ticker", "") for c in entities.get("companies", []) if c.get("ticker")]
    if companies:
        parts.append(f"Companies: {', '.join(companies[:10])}")
    geos = [g.get("name", "") for g in entities.get("geographies", []) if g.get("name")]
    if geos:
        parts.append(f"Geographies: {', '.join(geos[:8])}")
    insts = [i.get("name", "") for i in entities.get("institutions", []) if i.get("name")]
    if insts:
        parts.append(f"Institutions: {', '.join(insts[:8])}")
    persons = [p.get("name", "") for p in entities.get("persons", []) if p.get("name")]
    if persons:
        parts.append(f"Persons: {', '.join(persons[:8])}")
    sectors = [s for s in entities.get("sectors", []) if s]
    if sectors:
        parts.append(f"Sectors: {', '.join(sectors)}")
    return "\n".join(parts)


async def _call_openai(subject_type: str, user_prompt: str) -> dict | None:
    if not settings.OPENAI_API_KEY:
        logger.debug("[llm_analysis] No OpenAI key — skipping analysis")
        return None
    try:
        client = _get_client()
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT.replace("{subject_type}", subject_type)},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            timeout=60.0,
        )
        raw = response.choices[0].message.content or "{}"
        return json.loads(raw)
    except Exception as e:
        logger.error("[llm_analysis] OpenAI call failed: %s", e)
        return None


async def generate_event_analysis(
    event_id: str,
    event: dict,
    articles: list[dict],
    entities: dict,
) -> dict | None:
    cache_key = f"event:{event_id}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    articles_text = _build_articles_text(articles)
    entities_text = _build_entities_text(entities)
    user_prompt = (
        f"Event: {event.get('title', '')}\n"
        f"Type: {event.get('type', '')}\n"
        f"Date: {event.get('date', '')}\n"
        f"Description: {event.get('description', '')}\n\n"
        f"Entities:\n{entities_text}\n\n"
        f"Recent Articles:\n{articles_text}"
    )

    result = await _call_openai("event", user_prompt)
    if result is not None:
        _cache_set(cache_key, result)
    return result


async def generate_theme_analysis(
    theme_name: str,
    theme: dict,
    articles: list[dict],
    entities: dict,
) -> dict | None:
    cache_key = f"theme:{theme_name}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    articles_text = _build_articles_text(articles)
    entities_text = _build_entities_text(entities)
    user_prompt = (
        f"Macro Theme: {theme_name}\n"
        f"Description: {theme.get('description', '')}\n"
        f"Article count: {theme.get('article_count', 0)}\n\n"
        f"Entities:\n{entities_text}\n\n"
        f"Recent Articles:\n{articles_text}"
    )

    result = await _call_openai("macro theme", user_prompt)
    if result is not None:
        _cache_set(cache_key, result)
    return result
