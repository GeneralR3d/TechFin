"""APScheduler setup — registers the hourly Yahoo RSS ingestion job."""
import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.database import async_session
from app.services.news_fetcher import fetch_yahoo_rss
from app.services.graph_ingestion import upsert_raw_article, ingest_article_to_graph

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


async def _run_yahoo_rss_job() -> None:
    from app.models.ingestion_job import IngestionJob

    started_at = datetime.now(timezone.utc)
    articles_fetched = 0
    articles_new = 0
    articles_ingested = 0
    error_msg = None

    async with async_session() as db:
        job = IngestionJob(source="yahoo_rss", started_at=started_at, status="running")
        db.add(job)
        await db.flush()

        try:
            rows = fetch_yahoo_rss()
            articles_fetched = len(rows)

            for row in rows:
                is_new, record = await upsert_raw_article(
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
                )
                if is_new:
                    articles_new += 1

            await db.flush()

            # Graph ingestion for new articles
            for row in rows:
                if not row.get("_already_existed", False):
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
                        )
                        articles_ingested += 1
                    except Exception as e:
                        logger.warning("[scheduler] Graph ingest failed for %s: %s", row["news_id"], e)

            job.status = "completed"

        except Exception as e:
            error_msg = str(e)
            job.status = "failed"
            job.error = error_msg
            logger.error("[scheduler] Yahoo RSS job failed: %s", e)

        finally:
            job.completed_at = datetime.now(timezone.utc)
            job.articles_fetched = articles_fetched
            job.articles_new = articles_new
            job.articles_graph_ingested = articles_ingested
            await db.commit()

    logger.info(
        "[scheduler] Yahoo RSS job done: fetched=%s new=%s ingested=%s",
        articles_fetched, articles_new, articles_ingested,
    )


def get_scheduler() -> AsyncIOScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler(timezone="UTC")
        _scheduler.add_job(
            _run_yahoo_rss_job,
            trigger="interval",
            hours=1,
            id="yahoo_rss_ingest",
            replace_existing=True,
        )
    return _scheduler


async def start_scheduler() -> None:
    scheduler = get_scheduler()
    if not scheduler.running:
        scheduler.start()
        logger.info("[scheduler] APScheduler started")


async def stop_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("[scheduler] APScheduler stopped")
