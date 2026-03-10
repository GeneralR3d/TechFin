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
    from datetime import datetime, timedelta, timezone
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (e:Event)<-[:ABOUT]-(a:NewsArticle)
            WHERE a.published_at >= $since
            WITH e, count(a) AS article_count, avg(a.sentiment_score) AS avg_sentiment
            ORDER BY article_count DESC
            LIMIT $limit
            RETURN e.id AS id, e.title AS title, e.type AS type,
                   e.date AS date, e.description AS description,
                   article_count, avg_sentiment
            """,
            since=since,
            limit=limit,
        )
        return [dict(r) async for r in result]


async def get_active_themes(limit: int = 15, days: int = 7) -> list[dict]:
    from datetime import datetime, timedelta, timezone
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (t:MacroTheme)<-[:PART_OF_THEME]-(a:NewsArticle)
            WHERE a.published_at >= $since
            WITH t, count(a) AS article_count, avg(a.sentiment_score) AS avg_sentiment
            ORDER BY article_count DESC
            LIMIT $limit
            OPTIONAL MATCH (t)<-[:PART_OF_THEME]-(a2:NewsArticle)-[:MENTIONS]->(c:Company)
            WHERE a2.published_at >= $since AND c IS NOT NULL AND NOT c.ticker STARTS WITH '__'
            WITH t, article_count, avg_sentiment,
                 c.ticker AS ticker, count(a2) AS mention_count, avg(a2.sentiment_score) AS ticker_sentiment
            WHERE ticker IS NOT NULL
            WITH t, article_count, avg_sentiment,
                 {ticker: ticker, sentiment: ticker_sentiment, count: mention_count} AS ticker_data
            ORDER BY ticker_data.count DESC
            WITH t, article_count, avg_sentiment, collect(ticker_data)[0..3] AS top_tickers
            RETURN t.name AS name, t.description AS description,
                   article_count, avg_sentiment, top_tickers
            """,
            since=since,
            limit=limit,
        )
        return [dict(r) async for r in result]


async def get_articles_by_event(event_id: str, limit: int = 20) -> list[dict]:
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (e:Event {id: $event_id})<-[:ABOUT]-(a:NewsArticle)
            RETURN a.news_id AS news_id, a.title AS title, a.url AS url,
                   a.summary AS summary, a.published_at AS published_at,
                   a.source AS source, a.platform AS platform,
                   a.sentiment_score AS sentiment_score
            ORDER BY a.published_at DESC
            LIMIT $limit
            """,
            event_id=event_id,
            limit=limit,
        )
        return [dict(r) async for r in result]


async def get_event_entities(event_id: str) -> dict:
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (e:Event {id: $event_id})<-[:ABOUT]-(a:NewsArticle)
            OPTIONAL MATCH (a)-[:MENTIONS]->(c:Company)
            WHERE NOT c.ticker STARTS WITH '__'
            OPTIONAL MATCH (a)-[:MENTIONS]->(g:Geography)
            OPTIONAL MATCH (a)-[:MENTIONS]->(i:Institution)
            OPTIONAL MATCH (a)-[:MENTIONS]->(p:Person)
            OPTIONAL MATCH (a)-[:IN_SECTOR]->(s:Sector)
            OPTIONAL MATCH (a)-[:IN_INDUSTRY]->(ind:Industry)
            RETURN
              collect(DISTINCT {ticker: c.ticker, name: c.name}) AS companies,
              collect(DISTINCT {name: g.name, geo_type: g.geo_type}) AS geographies,
              collect(DISTINCT {name: i.name, inst_type: i.inst_type}) AS institutions,
              collect(DISTINCT {name: p.name, role: p.role}) AS persons,
              collect(DISTINCT s.name) AS sectors,
              collect(DISTINCT ind.name) AS industries
            """,
            event_id=event_id,
        )
        row = await result.single()
        if not row:
            return {"companies": [], "geographies": [], "institutions": [], "persons": [], "sectors": [], "industries": []}
        d = dict(row)
        # Filter out null entries from OPTIONAL MATCHes
        d["companies"] = [x for x in d.get("companies", []) if x.get("ticker")]
        d["geographies"] = [x for x in d.get("geographies", []) if x.get("name")]
        d["institutions"] = [x for x in d.get("institutions", []) if x.get("name")]
        d["persons"] = [x for x in d.get("persons", []) if x.get("name")]
        d["sectors"] = [x for x in d.get("sectors", []) if x]
        d["industries"] = [x for x in d.get("industries", []) if x]
        return d


async def get_theme_entities(theme_name: str) -> dict:
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (t:MacroTheme {name: $theme_name})<-[:PART_OF_THEME]-(a:NewsArticle)
            OPTIONAL MATCH (a)-[:MENTIONS]->(c:Company)
            WHERE NOT c.ticker STARTS WITH '__'
            OPTIONAL MATCH (a)-[:MENTIONS]->(g:Geography)
            OPTIONAL MATCH (a)-[:MENTIONS]->(i:Institution)
            OPTIONAL MATCH (a)-[:MENTIONS]->(p:Person)
            OPTIONAL MATCH (a)-[:IN_SECTOR]->(s:Sector)
            OPTIONAL MATCH (a)-[:IN_INDUSTRY]->(ind:Industry)
            RETURN
              collect(DISTINCT {ticker: c.ticker, name: c.name}) AS companies,
              collect(DISTINCT {name: g.name, geo_type: g.geo_type}) AS geographies,
              collect(DISTINCT {name: i.name, inst_type: i.inst_type}) AS institutions,
              collect(DISTINCT {name: p.name, role: p.role}) AS persons,
              collect(DISTINCT s.name) AS sectors,
              collect(DISTINCT ind.name) AS industries
            """,
            theme_name=theme_name,
        )
        row = await result.single()
        if not row:
            return {"companies": [], "geographies": [], "institutions": [], "persons": [], "sectors": [], "industries": []}
        d = dict(row)
        d["companies"] = [x for x in d.get("companies", []) if x.get("ticker")]
        d["geographies"] = [x for x in d.get("geographies", []) if x.get("name")]
        d["institutions"] = [x for x in d.get("institutions", []) if x.get("name")]
        d["persons"] = [x for x in d.get("persons", []) if x.get("name")]
        d["sectors"] = [x for x in d.get("sectors", []) if x]
        d["industries"] = [x for x in d.get("industries", []) if x]
        return d


async def get_articles_by_industry(industry_name: str, limit: int = 20) -> list[dict]:
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (i:Industry {name: $name})<-[:IN_INDUSTRY]-(a:NewsArticle)
            RETURN a.news_id AS news_id, a.title AS title, a.url AS url,
                   a.summary AS summary, a.published_at AS published_at,
                   a.source AS source, a.platform AS platform,
                   a.sentiment_score AS sentiment_score
            ORDER BY a.published_at DESC
            LIMIT $limit
            """,
            name=industry_name,
            limit=limit,
        )
        return [dict(r) async for r in result]


async def get_articles_by_geography(geo_name: str, limit: int = 20) -> list[dict]:
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (g:Geography {name: $name})<-[:MENTIONS]-(a:NewsArticle)
            RETURN a.news_id AS news_id, a.title AS title, a.url AS url,
                   a.summary AS summary, a.published_at AS published_at,
                   a.source AS source, a.platform AS platform,
                   a.sentiment_score AS sentiment_score
            ORDER BY a.published_at DESC
            LIMIT $limit
            """,
            name=geo_name,
            limit=limit,
        )
        return [dict(r) async for r in result]


async def get_articles_by_institution(inst_name: str, limit: int = 20) -> list[dict]:
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (i:Institution {name: $name})<-[:MENTIONS]-(a:NewsArticle)
            RETURN a.news_id AS news_id, a.title AS title, a.url AS url,
                   a.summary AS summary, a.published_at AS published_at,
                   a.source AS source, a.platform AS platform,
                   a.sentiment_score AS sentiment_score
            ORDER BY a.published_at DESC
            LIMIT $limit
            """,
            name=inst_name,
            limit=limit,
        )
        return [dict(r) async for r in result]


async def get_articles_by_person(person_name: str, limit: int = 20) -> list[dict]:
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (p:Person {name: $name})<-[:MENTIONS]-(a:NewsArticle)
            RETURN a.news_id AS news_id, a.title AS title, a.url AS url,
                   a.summary AS summary, a.published_at AS published_at,
                   a.source AS source, a.platform AS platform,
                   a.sentiment_score AS sentiment_score
            ORDER BY a.published_at DESC
            LIMIT $limit
            """,
            name=person_name,
            limit=limit,
        )
        return [dict(r) async for r in result]


async def get_articles_by_entity(entity_type: str, entity_name: str, limit: int = 20) -> list[dict]:
    """Dispatch to the appropriate article query by entity type."""
    if entity_type == "company":
        return await get_articles_by_company(entity_name.upper(), limit)
    elif entity_type == "sector":
        return await get_articles_by_sector(entity_name, limit)
    elif entity_type == "theme":
        return await get_articles_by_theme(entity_name, limit)
    elif entity_type == "industry":
        return await get_articles_by_industry(entity_name, limit)
    elif entity_type == "geography":
        return await get_articles_by_geography(entity_name, limit)
    elif entity_type == "institution":
        return await get_articles_by_institution(entity_name, limit)
    elif entity_type == "person":
        return await get_articles_by_person(entity_name, limit)
    return []


async def get_related_entities_for_entity(entity_type: str, entity_name: str) -> dict:
    """Two-hop: find all articles linked to entity, collect all related entity types."""
    driver = get_driver()

    # Build the initial MATCH clause depending on entity type
    match_clauses = {
        "company": "MATCH (e:Company {ticker: $name})<-[:MENTIONS]-(a:NewsArticle)",
        "sector": "MATCH (e:Sector {name: $name})<-[:IN_SECTOR]-(a:NewsArticle)",
        "industry": "MATCH (e:Industry {name: $name})<-[:IN_INDUSTRY]-(a:NewsArticle)",
        "geography": "MATCH (e:Geography {name: $name})<-[:MENTIONS]-(a:NewsArticle)",
        "institution": "MATCH (e:Institution {name: $name})<-[:MENTIONS]-(a:NewsArticle)",
        "person": "MATCH (e:Person {name: $name})<-[:MENTIONS]-(a:NewsArticle)",
        "theme": "MATCH (e:MacroTheme {name: $name})<-[:PART_OF_THEME]-(a:NewsArticle)",
    }
    match_clause = match_clauses.get(entity_type, "MATCH (e {name: $name})<--(a:NewsArticle)")

    async with driver.session() as session:
        result = await session.run(
            f"""
            {match_clause}
            OPTIONAL MATCH (a)-[:MENTIONS]->(c:Company)
            WHERE NOT c.ticker STARTS WITH '__'
            OPTIONAL MATCH (a)-[:MENTIONS]->(g:Geography)
            OPTIONAL MATCH (a)-[:MENTIONS]->(i:Institution)
            OPTIONAL MATCH (a)-[:MENTIONS]->(p:Person)
            OPTIONAL MATCH (a)-[:IN_SECTOR]->(s:Sector)
            OPTIONAL MATCH (a)-[:IN_INDUSTRY]->(ind:Industry)
            RETURN
              collect(DISTINCT {{ticker: c.ticker, name: c.name}}) AS companies,
              collect(DISTINCT {{name: g.name, geo_type: g.geo_type}}) AS geographies,
              collect(DISTINCT {{name: i.name, inst_type: i.inst_type}}) AS institutions,
              collect(DISTINCT {{name: p.name, role: p.role}}) AS persons,
              collect(DISTINCT s.name) AS sectors,
              collect(DISTINCT ind.name) AS industries
            """,
            name=entity_name,
        )
        row = await result.single()
        if not row:
            return {"companies": [], "geographies": [], "institutions": [], "persons": [], "sectors": [], "industries": []}
        d = dict(row)
        d["companies"] = [x for x in d.get("companies", []) if x.get("ticker")]
        d["geographies"] = [x for x in d.get("geographies", []) if x.get("name")]
        d["institutions"] = [x for x in d.get("institutions", []) if x.get("name")]
        d["persons"] = [x for x in d.get("persons", []) if x.get("name")]
        d["sectors"] = [x for x in d.get("sectors", []) if x]
        d["industries"] = [x for x in d.get("industries", []) if x]
        return d


async def find_events_by_name(name: str, limit: int = 5) -> list[dict]:
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (e:Event)
            WHERE toLower(e.title) CONTAINS toLower($name)
            RETURN e.id AS id, e.title AS title, e.type AS type, e.date AS date
            ORDER BY e.title
            LIMIT $limit
            """,
            name=name,
            limit=limit,
        )
        return [dict(r) async for r in result]


async def find_themes_by_name(name: str, limit: int = 5) -> list[dict]:
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (t:MacroTheme)
            WHERE toLower(t.name) CONTAINS toLower($name)
            RETURN t.name AS name
            ORDER BY t.name
            LIMIT $limit
            """,
            name=name,
            limit=limit,
        )
        return [dict(r) async for r in result]


async def get_existing_context_nodes(limit: int = 30) -> dict:
    """Return top MacroTheme names and recent Event titles for LLM context injection."""
    try:
        driver = get_driver()
        async with driver.session() as session:
            theme_result = await session.run(
                """
                MATCH (t:MacroTheme)<-[:PART_OF_THEME]-()
                RETURN t.name AS name, count(*) AS cnt
                ORDER BY cnt DESC
                LIMIT $limit
                """,
                limit=limit,
            )
            macro_themes = [r["name"] async for r in theme_result]

            from datetime import datetime, timedelta, timezone
            since = datetime.now(timezone.utc) - timedelta(days=30)
            event_result = await session.run(
                """
                MATCH (e:Event)<-[:ABOUT]-(a:NewsArticle)
                WHERE a.published_at >= $since
                RETURN DISTINCT e.title AS title
                LIMIT $limit
                """,
                since=since.isoformat(),
                limit=limit,
            )
            events = [r["title"] async for r in event_result]

        return {"macro_themes": macro_themes, "events": events}
    except Exception as e:
        logger.debug("[graph_queries] Could not fetch context nodes: %s", e)
        return {"macro_themes": [], "events": []}


async def get_sector_heatmap() -> list[dict]:
    from datetime import datetime, timedelta, timezone
    since = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (s:Sector)<-[:IN_SECTOR]-(a:NewsArticle)
            WHERE a.published_at >= $since
            WITH s.name AS sector,
                 count(a) AS article_count,
                 avg(a.sentiment_score) AS avg_sentiment
            ORDER BY article_count DESC
            RETURN sector, article_count, avg_sentiment
            """,
            since=since,
        )
        return [dict(r) async for r in result]
