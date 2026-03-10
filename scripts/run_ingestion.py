"""Standalone ingestion pipeline: RSS fetch → PG upsert → LLM extraction → Neo4j MERGE.

Usage (from repo root):
    cd backend && uv run python ../scripts/run_ingestion.py
"""
import asyncio
import logging
import os
import sys
from pathlib import Path

# Load .env before importing app modules so Settings picks up the values.
from dotenv import load_dotenv

_env_path = Path(__file__).parent.parent / "backend" / ".env"
load_dotenv(_env_path)

# Ensure the backend package is importable.
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("run_ingestion")


async def main() -> None:
    # Import after env is loaded so Settings resolves correctly.
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

    from app.config import settings
    from app.database_graph import create_constraints, close_driver
    from app.services.alphavantage_news import fetch_alphavantage_news
    from app.services.graph_ingestion import upsert_raw_article, ingest_article_to_graph

    # --- PostgreSQL ---
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    # --- Neo4j ---
    await create_constraints()

    articles_fetched = 0
    articles_new = 0
    articles_ingested = 0

    async with session_factory() as db:
        try:
            rows = await fetch_alphavantage_news()
            articles_fetched = len(rows)
            logger.info("Fetched %d articles from AlphaVantage", articles_fetched)

            new_ids: set[str] = set()
            for row in rows:
                is_new, _ = await upsert_raw_article(
                    db=db,
                    news_id=row["news_id"],
                    title=row["title"],
                    url=row["url"],
                    summary=row.get("summary"),
                    published_at=row["published_at"],
                    source=row["source"],
                    platform=row["platform"],
                    ticker_hint=row.get("ticker_hint"),
                    raw_tags=row.get("raw_tags", []),
                    sentiment_score=row.get("sentiment_score"),
                    ticker_sentiment=row.get("ticker_sentiment"),
                )
                if is_new:
                    articles_new += 1
                    new_ids.add(row["news_id"])

            await db.flush()
            logger.info("Upserted to PG: %d new / %d total", articles_new, articles_fetched)

            semaphore = asyncio.Semaphore(25)
            db_lock = asyncio.Lock()

            async def _process_row(row: dict) -> None:
                nonlocal articles_ingested
                async with semaphore:
                    try:
                        await ingest_article_to_graph(
                            news_id=row["news_id"],
                            title=row["title"],
                            content=row.get("summary", ""),
                            url=row["url"],
                            summary=row.get("summary"),
                            published_at=row["published_at"],
                            source=row["source"],
                            platform=row["platform"],
                            db=db,
                            db_lock=db_lock,
                        )
                        async with db_lock:
                            articles_ingested += 1
                    except Exception as e:
                        logger.warning("Graph ingest failed for %s: %s", row["news_id"], e)

            tasks = [
                _process_row(row)
                for row in rows
                if row["news_id"] in new_ids
            ]

            if tasks:
                await asyncio.gather(*tasks)

            await db.commit()

        except Exception:
            logger.exception("Ingestion pipeline failed")
            await db.rollback()
            raise

    await engine.dispose()
    await close_driver()

    print(f"\nDone: fetched={articles_fetched} new={articles_new} ingested={articles_ingested}")


if __name__ == "__main__":
    asyncio.run(main())
