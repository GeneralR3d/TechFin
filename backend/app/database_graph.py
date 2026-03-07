import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from neo4j import AsyncGraphDatabase, AsyncDriver

from app.config import settings

logger = logging.getLogger(__name__)

_driver: AsyncDriver | None = None


def get_driver() -> AsyncDriver:
    global _driver
    if _driver is None:
        _driver = AsyncGraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD),
        )
    return _driver


async def close_driver() -> None:
    global _driver
    if _driver is not None:
        await _driver.close()
        _driver = None


@asynccontextmanager
async def get_neo4j() -> AsyncGenerator[AsyncDriver, None]:
    driver = get_driver()
    yield driver


CONSTRAINTS = [
    "CREATE CONSTRAINT macrotheme_name IF NOT EXISTS FOR (n:MacroTheme) REQUIRE n.name IS UNIQUE",
    "CREATE CONSTRAINT event_id IF NOT EXISTS FOR (n:Event) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT newsarticle_id IF NOT EXISTS FOR (n:NewsArticle) REQUIRE n.news_id IS UNIQUE",
    "CREATE CONSTRAINT socialpost_id IF NOT EXISTS FOR (n:SocialPost) REQUIRE n.post_id IS UNIQUE",
    "CREATE CONSTRAINT sector_name IF NOT EXISTS FOR (n:Sector) REQUIRE n.name IS UNIQUE",
    "CREATE CONSTRAINT industry_name IF NOT EXISTS FOR (n:Industry) REQUIRE n.name IS UNIQUE",
    "CREATE CONSTRAINT company_ticker IF NOT EXISTS FOR (n:Company) REQUIRE n.ticker IS UNIQUE",
    "CREATE CONSTRAINT indicator_name IF NOT EXISTS FOR (n:Indicator) REQUIRE n.name IS UNIQUE",
    "CREATE CONSTRAINT geography_name IF NOT EXISTS FOR (n:Geography) REQUIRE n.name IS UNIQUE",
    "CREATE CONSTRAINT institution_name IF NOT EXISTS FOR (n:Institution) REQUIRE n.name IS UNIQUE",
    "CREATE CONSTRAINT person_name IF NOT EXISTS FOR (n:Person) REQUIRE n.name IS UNIQUE",
]


async def create_constraints() -> None:
    if not settings.NEO4J_PASSWORD:
        logger.warning("[neo4j] NEO4J_PASSWORD not set — skipping constraint creation")
        return
    try:
        driver = get_driver()
        async with driver.session() as session:
            for stmt in CONSTRAINTS:
                await session.run(stmt)
        logger.info("[neo4j] Constraints created/verified")
    except Exception as e:
        logger.error("[neo4j] Failed to create constraints: %s", e)
