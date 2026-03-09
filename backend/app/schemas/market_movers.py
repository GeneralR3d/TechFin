from pydantic import BaseModel


class MoverStock(BaseModel):
    ticker: str
    price: str
    change_amount: str
    change_percentage: str
    volume: str


class MarketMoversResponse(BaseModel):
    top_gainers: list[MoverStock]
    top_losers: list[MoverStock]
    most_active: list[MoverStock]
