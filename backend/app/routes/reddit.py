import logging
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, Query

from app.auth import get_current_user
from app.models.user import User
from app.schemas.social import SocialPostResponse
from app.services.reddit import fetch_reddit_posts
from app.services.graph_ingestion import upsert_raw_article, ingest_article_to_graph

router = APIRouter(prefix="/api/reddit", tags=["reddit"])
logger = logging.getLogger(__name__)


async def _background_ingest(posts: list[dict]) -> None:
    from app.database import async_session
    async with async_session() as db:
        for post in posts:
            try:
                published_at = _parse_datetime(post.get("published_at", ""))
                is_new, _ = await upsert_raw_article(
                    db=db,
                    news_id=post["id"],
                    title=post.get("content", "")[:255],
                    url=post["url"],
                    summary=post.get("content"),
                    published_at=published_at,
                    source="reddit",
                    platform="reddit",
                )
                if is_new:
                    await ingest_article_to_graph(
                        news_id=post["id"],
                        title=post.get("content", "")[:255],
                        content=post.get("content", ""),
                        url=post["url"],
                        summary=post.get("content"),
                        published_at=published_at,
                        source="reddit",
                        platform="reddit",
                        db=db,
                    )
            except Exception as e:
                logger.warning("[reddit] Background ingest failed for %s: %s", post.get("id"), e)
        await db.commit()


def _parse_datetime(dt_str: str) -> datetime:
    try:
        return datetime.fromisoformat(dt_str)
    except Exception:
        return datetime.now(timezone.utc)


@router.get("", response_model=list[SocialPostResponse])
async def get_reddit_posts(
    background_tasks: BackgroundTasks,
    subreddit: str = Query("stocks", description="Subreddit name"),
    user: User = Depends(get_current_user),
):
    posts = await fetch_reddit_posts(subreddit)
    background_tasks.add_task(_background_ingest, posts)
    return posts
