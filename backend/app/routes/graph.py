import asyncio

from fastapi import APIRouter, Depends, HTTPException

from app.auth import get_current_user
from app.models.user import User
from app.services import graph_queries
from app.services import llm_analysis

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


@router.get("/events/{event_id}/articles")
async def event_articles(
    event_id: str,
    limit: int = 20,
    user: User = Depends(get_current_user),
):
    try:
        return await graph_queries.get_articles_by_event(event_id, limit)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Graph query failed: {e}")


@router.get("/events/{event_id}/entities")
async def event_entities(
    event_id: str,
    user: User = Depends(get_current_user),
):
    try:
        return await graph_queries.get_event_entities(event_id)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Graph query failed: {e}")


@router.get("/events/{event_id}/analysis")
async def event_analysis(
    event_id: str,
    user: User = Depends(get_current_user),
):
    try:
        articles, entities = await asyncio.gather(
            graph_queries.get_articles_by_event(event_id, 20),
            graph_queries.get_event_entities(event_id),
        )
        if not articles:
            raise HTTPException(status_code=404, detail="Event not found or has no articles")
        # Build a minimal event dict from the first article context
        # (full event data comes from the events/recent endpoint)
        event = {"title": event_id, "type": "", "date": "", "description": ""}
        result = await llm_analysis.generate_event_analysis(event_id, event, articles, entities)
        if result is None:
            return None
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Analysis failed: {e}")


@router.get("/themes/active")
async def active_themes(
    limit: int = 15,
    user: User = Depends(get_current_user),
):
    try:
        return await graph_queries.get_active_themes(limit)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Graph query failed: {e}")


@router.get("/themes/{theme_name}/entities")
async def theme_entities(
    theme_name: str,
    user: User = Depends(get_current_user),
):
    try:
        return await graph_queries.get_theme_entities(theme_name)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Graph query failed: {e}")


@router.get("/themes/{theme_name}/analysis")
async def theme_analysis(
    theme_name: str,
    user: User = Depends(get_current_user),
):
    try:
        articles, entities = await asyncio.gather(
            graph_queries.get_articles_by_theme(theme_name, 20),
            graph_queries.get_theme_entities(theme_name),
        )
        if not articles:
            raise HTTPException(status_code=404, detail="Theme not found or has no articles")
        theme = {"description": ""}
        result = await llm_analysis.generate_theme_analysis(theme_name, theme, articles, entities)
        if result is None:
            return None
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Analysis failed: {e}")


@router.get("/heatmap")
async def sector_heatmap(user: User = Depends(get_current_user)):
    try:
        return await graph_queries.get_sector_heatmap()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Graph query failed: {e}")


VALID_ENTITY_TYPES = {"company", "sector", "industry", "geography", "institution", "person"}


@router.get("/entity/{entity_type}/{entity_name}/articles")
async def entity_articles(
    entity_type: str,
    entity_name: str,
    limit: int = 30,
    user: User = Depends(get_current_user),
):
    if entity_type not in VALID_ENTITY_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid entity type: {entity_type}")
    try:
        return await graph_queries.get_articles_by_entity(entity_type, entity_name, limit)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Graph query failed: {e}")


@router.get("/entity/{entity_type}/{entity_name}/related")
async def entity_related(
    entity_type: str,
    entity_name: str,
    user: User = Depends(get_current_user),
):
    if entity_type not in VALID_ENTITY_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid entity type: {entity_type}")
    try:
        return await graph_queries.get_related_entities_for_entity(entity_type, entity_name)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Graph query failed: {e}")
