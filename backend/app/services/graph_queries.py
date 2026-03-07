"""Cypher query functions for the graph API endpoints."""
import logging

from app.database_graph import get_driver

logger = logging.getLogger(__name__)


async def get_articles_by_company(ticker: str, limit: int = 20) -> list[dict]:
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (c:Company {ticker: $ticker})<-[:MENTIONS]-(a:NewsArticle)
            RETURN a.news_id AS news_id, a.title AS title, a.url AS url,
                   a.summary AS summary, a.published_at AS published_at,
                   a.source AS source, a.platform AS platform,
                   a.sentiment_score AS sentiment_score
            ORDER BY a.published_at DESC
            LIMIT $limit
            """,
            ticker=ticker,
            limit=limit,
        )
        return [dict(r) async for r in result]


async def get_articles_by_sector(sector: str, limit: int = 20) -> list[dict]:
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (s:Sector {name: $sector})<-[:IN_SECTOR]-(a:NewsArticle)
            RETURN a.news_id AS news_id, a.title AS title, a.url AS url,
                   a.summary AS summary, a.published_at AS published_at,
                   a.source AS source, a.platform AS platform,
                   a.sentiment_score AS sentiment_score
            ORDER BY a.published_at DESC
            LIMIT $limit
            """,
            sector=sector,
            limit=limit,
        )
        return [dict(r) async for r in result]


async def get_articles_by_theme(theme_name: str, limit: int = 20) -> list[dict]:
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (t:MacroTheme {name: $name})<-[:PART_OF_THEME]-(a:NewsArticle)
            RETURN a.news_id AS news_id, a.title AS title, a.url AS url,
                   a.summary AS summary, a.published_at AS published_at,
                   a.source AS source, a.platform AS platform,
                   a.sentiment_score AS sentiment_score
            ORDER BY a.published_at DESC
            LIMIT $limit
            """,
            name=theme_name,
            limit=limit,
        )
        return [dict(r) async for r in result]


async def get_linked_articles(news_id: str, limit: int = 10) -> list[dict]:
    """Articles sharing companies, sectors, or themes with the given article."""
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (a:NewsArticle {news_id: $news_id})-[:MENTIONS|IN_SECTOR|IN_INDUSTRY|PART_OF_THEME]->(shared)
            MATCH (b:NewsArticle)-[:MENTIONS|IN_SECTOR|IN_INDUSTRY|PART_OF_THEME]->(shared)
            WHERE b.news_id <> $news_id
            WITH b, count(shared) AS shared_count
            ORDER BY shared_count DESC, b.published_at DESC
            LIMIT $limit
            RETURN b.news_id AS news_id, b.title AS title, b.url AS url,
                   b.summary AS summary, b.published_at AS published_at,
                   b.source AS source, b.platform AS platform,
                   b.sentiment_score AS sentiment_score,
                   shared_count
            """,
            news_id=news_id,
            limit=limit,
        )
        return [dict(r) async for r in result]


async def get_recent_events(days: int = 7, limit: int = 20) -> list[dict]:
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (e:Event)<-[:ABOUT]-(a:NewsArticle)
            WHERE a.published_at >= datetime() - duration({days: $days})
            WITH e, count(a) AS article_count
            ORDER BY article_count DESC
            LIMIT $limit
            RETURN e.id AS id, e.title AS title, e.type AS type,
                   e.date AS date, e.description AS description,
                   article_count
            """,
            days=days,
            limit=limit,
        )
        return [dict(r) async for r in result]


async def get_active_themes(limit: int = 15) -> list[dict]:
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (t:MacroTheme)<-[:PART_OF_THEME]-(a:NewsArticle)
            WITH t, count(a) AS article_count, avg(a.sentiment_score) AS avg_sentiment
            ORDER BY article_count DESC
            LIMIT $limit
            RETURN t.name AS name, t.description AS description,
                   article_count, avg_sentiment
            """,
            limit=limit,
        )
        return [dict(r) async for r in result]


async def get_sector_heatmap() -> list[dict]:
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (s:Sector)<-[:IN_SECTOR]-(a:NewsArticle)
            WHERE a.published_at >= datetime() - duration({days: 7})
            WITH s.name AS sector,
                 count(a) AS article_count,
                 avg(a.sentiment_score) AS avg_sentiment
            ORDER BY article_count DESC
            RETURN sector, article_count, avg_sentiment
            """
        )
        return [dict(r) async for r in result]
