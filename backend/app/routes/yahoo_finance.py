import logging
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.article import ArticleResponse
from app.services.yahoo_finance import fetch_yahoo_finance_news
from app.services.graph_ingestion import upsert_raw_article, ingest_article_to_graph

router = APIRouter(prefix="/api/yahoo-finance", tags=["yahoo-finance"])
logger = logging.getLogger(__name__)


async def _background_ingest(articles: list[dict]) -> None:
    from app.database import async_session
    async with async_session() as db:
        for article in articles:
            try:
                published_at = _parse_datetime(article.get("published_at", ""))
                is_new, _ = await upsert_raw_article(
                    db=db,
                    news_id=article["id"],
                    title=article["title"],
                    url=article["url"],
                    summary=article.get("summary"),
                    published_at=published_at,
                    source="yahoo_finance",
                    platform="yahoo_finance",
                )
                if is_new:
                    await ingest_article_to_graph(
                        news_id=article["id"],
                        title=article["title"],
                        content=article.get("summary", ""),
                        url=article["url"],
                        summary=article.get("summary"),
                        published_at=published_at,
                        source="yahoo_finance",
                        platform="yahoo_finance",
                        db=db,
                    )
            except Exception as e:
                logger.warning("[yahoo-finance] Background ingest failed for %s: %s", article.get("id"), e)
        await db.commit()


def _parse_datetime(dt_str: str) -> datetime:
    try:
        return datetime.fromisoformat(dt_str)
    except Exception:
        return datetime.now(timezone.utc)


@router.get("", response_model=list[ArticleResponse])
async def get_yahoo_finance_news(
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
):
    articles = await fetch_yahoo_finance_news()
    background_tasks.add_task(_background_ingest, articles)
    return articles
