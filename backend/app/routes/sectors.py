from fastapi import APIRouter, Depends

from app.auth import get_current_user
from app.models.user import User
from app.schemas.sectors import SectorData
from app.services.sectors import fetch_sector_data

router = APIRouter(prefix="/api/sectors", tags=["sectors"])


@router.get("", response_model=list[SectorData])
async def get_sectors(user: User = Depends(get_current_user)):
    return await fetch_sector_data()
