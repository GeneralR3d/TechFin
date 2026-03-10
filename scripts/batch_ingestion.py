"""Standalone batch ingestion pipeline for historical data (2025-2026).

Usage (from repo root):
    cd backend && uv run python ../scripts/batch_ingestion.py
"""
import asyncio
import logging
import sys
import calendar
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

_env_path = Path(__file__).parent.parent / "backend" / ".env"
load_dotenv(_env_path)

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("batch_ingestion")


def generate_monthly_ranges(start_year: int, end_year: int, end_month: int):
    """Generate AlphaVantage compatible time ranges by month."""
    ranges = []
    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            if year == end_year and month > end_month:
                break
            
            last_day = calendar.monthrange(year, month)[1]
            time_from = f"{year}{month:02d}01T0000"
            time_to = f"{year}{month:02d}{last_day:02d}T2359"
            ranges.append((time_from, time_to))
            
    return ranges


async def main() -> None:
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    
    from app.config import settings
    from app.database_graph import create_constraints, close_driver
    from app.services.alphavantage_news import fetch_alphavantage_news
    from app.services.graph_ingestion import upsert_raw_article, ingest_article_to_graph

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    await create_constraints()

    # Generate ranges for 2025 and 2026 up to current month (March 2026)
    now = datetime.now()
    end_year = now.year
    end_month = now.month
    
    start_year = 2025
    if end_year < start_year:
        end_year = start_year 

    date_ranges = generate_monthly_ranges(start_year, end_year, end_month)
    logger.info("Generated %d monthly batches to fetch", len(date_ranges))

    total_fetched = 0
    total_new = 0
    total_ingested = 0

    async with session_factory() as db:
        try:
            for time_from, time_to in date_ranges:
                logger.info("=== Fetching batch: %s to %s ===", time_from, time_to)
                
                rows = await fetch_alphavantage_news(
                    time_from=time_from, 
                    time_to=time_to
                )
                
                if not rows:
                    logger.info("No articles found or hit limit for this batch.")
                    continue
                    
                total_fetched += len(rows)
                logger.info("Fetched %d articles", len(rows))

                # PG Upsert
                new_ids: set[str] = set()
                batch_new = 0
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
                        batch_new += 1
                        total_new += 1
                        new_ids.add(row["news_id"])

                await db.flush()
                logger.info("Upserted to PG: %d new / %d total in this batch", batch_new, len(rows))

                # Graph Ingestion (Parallel)
                semaphore = asyncio.Semaphore(25)
                db_lock = asyncio.Lock()
                batch_ingested = 0

                async def _process_row(row: dict) -> None:
                    nonlocal batch_ingested, total_ingested
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
                                batch_ingested += 1
                                total_ingested += 1
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
                logger.info("Batch completed: ingested %d into graph", batch_ingested)

        except Exception:
            logger.exception("Batch ingestion pipeline failed")
            await db.rollback()
            raise

    await engine.dispose()
    await close_driver()

    print(f"\nDone: fetched_total={total_fetched} new_total={total_new} ingested_total={total_ingested}")


if __name__ == "__main__":
    asyncio.run(main())
