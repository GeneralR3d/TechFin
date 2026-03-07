from fastapi import APIRouter, Depends, HTTPException

from app.auth import get_current_user
from app.models.user import User
from app.services import graph_queries

router = APIRouter(prefix="/api/graph", tags=["graph"])


@router.get("/news/company/{ticker}")
async def articles_by_company(
    ticker: str,
    limit: int = 20,
    user: User = Depends(get_current_user),
):
    try:
        return await graph_queries.get_articles_by_company(ticker.upper(), limit)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Graph query failed: {e}")


@router.get("/news/sector/{sector}")
async def articles_by_sector(
    sector: str,
    limit: int = 20,
    # user: User = Depends(get_current_user),
):
    try:
        return await graph_queries.get_articles_by_sector(sector, limit)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Graph query failed: {e}")


@router.get("/news/theme/{theme_name}")
async def articles_by_theme(
    theme_name: str,
    limit: int = 20,
    user: User = Depends(get_current_user),
):
    try:
        return await graph_queries.get_articles_by_theme(theme_name, limit)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Graph query failed: {e}")


@router.get("/news/linked/{news_id}")
async def linked_articles(
    news_id: str,
    limit: int = 10,
    user: User = Depends(get_current_user),
):
    try:
        return await graph_queries.get_linked_articles(news_id, limit)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Graph query failed: {e}")


@router.get("/events/recent")
async def recent_events(
    days: int = 7,
    limit: int = 20,
    user: User = Depends(get_current_user),
):
    try:
        return await graph_queries.get_recent_events(days, limit)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Graph query failed: {e}")


@router.get("/themes/active")
async def active_themes(
    limit: int = 15,
    user: User = Depends(get_current_user),
):
    try:
        return await graph_queries.get_active_themes(limit)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Graph query failed: {e}")


@router.get("/heatmap")
async def sector_heatmap(user: User = Depends(get_current_user)):
    try:
        return await graph_queries.get_sector_heatmap()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Graph query failed: {e}")
