import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database_graph import get_driver
from app.services.llm_extraction import extract_entities

logger = logging.getLogger(__name__)


async def ingest_article_to_graph(
    news_id: str,
    title: str,
    content: str,
    url: str,
    summary: str | None,
    published_at: datetime,
    source: str,
    platform: str,
    db: AsyncSession,
) -> None:
    """Extract entities via LLM and MERGE them into Neo4j, then mark PG record as ingested."""
    entities = await extract_entities(title, content or summary or "")

    sentiment_score = entities.get("sentiment_score", 0.0)
    article_summary = entities.get("summary") or summary or ""

    driver = get_driver()
    async with driver.session() as session:
        # MERGE the NewsArticle node
        await session.run(
            """
            MERGE (a:NewsArticle {news_id: $news_id})
            SET a.title = $title,
                a.url = $url,
                a.summary = $summary,
                a.published_at = $published_at,
                a.source = $source,
                a.platform = $platform,
                a.sentiment_score = $sentiment_score
            """,
            news_id=news_id,
            title=title,
            url=url,
            summary=article_summary,
            published_at=published_at.isoformat(),
            source=source,
            platform=platform,
            sentiment_score=sentiment_score,
        )

        # MacroThemes
        for theme in entities.get("macro_themes", []):
            await session.run(
                """
                MERGE (t:MacroTheme {name: $name})
                ON CREATE SET t.description = $description, t.created_at = $now
                WITH t
                MATCH (a:NewsArticle {news_id: $news_id})
                MERGE (a)-[:PART_OF_THEME]->(t)
                """,
                name=theme["name"],
                description=theme.get("description", ""),
                now=datetime.now(timezone.utc).isoformat(),
                news_id=news_id,
            )

        # Events
        for event in entities.get("events", []):
            event_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"event:{event['title']}"))
            await session.run(
                """
                MERGE (e:Event {id: $id})
                ON CREATE SET e.title = $title,
                              e.type = $type,
                              e.date = $date,
                              e.description = $description
                WITH e
                MATCH (a:NewsArticle {news_id: $news_id})
                MERGE (a)-[:ABOUT]->(e)
                """,
                id=event_id,
                title=event["title"],
                type=event.get("type", "other"),
                date=event.get("date"),
                description=event.get("description", ""),
                news_id=news_id,
            )

        # Companies
        for company in entities.get("companies", []):
            ticker = company.get("ticker") or f"__name__{company['name']}"
            await session.run(
                """
                MERGE (c:Company {ticker: $ticker})
                ON CREATE SET c.name = $name
                WITH c
                MATCH (a:NewsArticle {news_id: $news_id})
                MERGE (a)-[:MENTIONS]->(c)
                """,
                ticker=ticker,
                name=company["name"],
                news_id=news_id,
            )

        # Sectors
        for sector in entities.get("sectors", []):
            await session.run(
                """
                MERGE (s:Sector {name: $name})
                WITH s
                MATCH (a:NewsArticle {news_id: $news_id})
                MERGE (a)-[:IN_SECTOR]->(s)
                """,
                name=sector,
                news_id=news_id,
            )

        # Industries
        for industry in entities.get("industries", []):
            await session.run(
                """
                MERGE (i:Industry {name: $name})
                WITH i
                MATCH (a:NewsArticle {news_id: $news_id})
                MERGE (a)-[:IN_INDUSTRY]->(i)
                """,
                name=industry,
                news_id=news_id,
            )

        # Indicators
        for indicator in entities.get("indicators", []):
            await session.run(
                """
                MERGE (ind:Indicator {name: $name})
                ON CREATE SET ind.type = $type
                """,
                name=indicator["name"],
                type=indicator.get("type", "other"),
            )

        # Geographies
        for geo in entities.get("geographies", []):
            await session.run(
                """
                MERGE (g:Geography {name: $name})
                ON CREATE SET g.geo_type = $geo_type
                WITH g
                MATCH (a:NewsArticle {news_id: $news_id})
                MERGE (a)-[:MENTIONS]->(g)
                """,
                name=geo["name"],
                geo_type=geo.get("geo_type", "country"),
                news_id=news_id,
            )

        # Institutions
        for inst in entities.get("institutions", []):
            await session.run(
                """
                MERGE (i:Institution {name: $name})
                ON CREATE SET i.inst_type = $inst_type
                WITH i
                MATCH (a:NewsArticle {news_id: $news_id})
                MERGE (a)-[:MENTIONS]->(i)
                """,
                name=inst["name"],
                inst_type=inst.get("inst_type", "other"),
                news_id=news_id,
            )

        # Persons
        for person in entities.get("persons", []):
            await session.run(
                """
                MERGE (p:Person {name: $name})
                ON CREATE SET p.role = $role
                WITH p
                MATCH (a:NewsArticle {news_id: $news_id})
                MERGE (a)-[:MENTIONS]->(p)
                """,
                name=person["name"],
                role=person.get("role"),
                news_id=news_id,
            )

    # Mark as graph-ingested in PostgreSQL
    from app.models.raw_news import RawNewsArticle
    result = await db.execute(
        select(RawNewsArticle).where(RawNewsArticle.news_id == news_id)
    )
    record = result.scalar_one_or_none()
    if record:
        record.graph_ingested = True
        record.graph_ingested_at = datetime.now(timezone.utc)

    logger.info("[graph] Ingested article %s", news_id)


async def upsert_raw_article(
    db: AsyncSession,
    news_id: str,
    title: str,
    url: str,
    summary: str | None,
    published_at: datetime,
    source: str,
    platform: str,
    ticker_hint: str | None = None,
    raw_tags: list[str] | None = None,
) -> tuple[bool, "RawNewsArticle"]:  # noqa: F821
    """Insert into raw_news_articles if not exists. Returns (is_new, record)."""
    from app.models.raw_news import RawNewsArticle

    result = await db.execute(
        select(RawNewsArticle).where(RawNewsArticle.news_id == news_id)
    )
    existing = result.scalar_one_or_none()
    if existing:
        return False, existing

    record = RawNewsArticle(
        news_id=news_id,
        title=title,
        url=url,
        summary=summary,
        published_at=published_at,
        source=source,
        platform=platform,
        ticker_hint=ticker_hint,
        raw_tags=raw_tags or [],
    )
    db.add(record)
    await db.flush()
    return True, record
