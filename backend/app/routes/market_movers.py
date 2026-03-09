from fastapi import APIRouter, Depends

from app.auth import get_current_user
from app.models.user import User
from app.schemas.market_movers import MarketMoversResponse
from app.services.market_movers import fetch_market_movers

router = APIRouter(prefix="/api/market", tags=["market"])


@router.get("/movers", response_model=MarketMoversResponse)
async def get_market_movers(user: User = Depends(get_current_user)):
    return await fetch_market_movers()
