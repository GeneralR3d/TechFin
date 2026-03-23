from pydantic import BaseModel


class SectorData(BaseModel):
    symbol: str
    name: str
    week_return: float
    ytd_return: float
    market_weight: float
    price: float
