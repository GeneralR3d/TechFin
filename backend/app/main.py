from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import auth, holdings, tickers, user, suggestions, yahoo_finance, reddit, social, sentiment, sectors, market_movers


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    yield


app = FastAPI(title="TechFin API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(holdings.router)
app.include_router(tickers.router)
app.include_router(user.router)
app.include_router(suggestions.router)
app.include_router(yahoo_finance.router)
app.include_router(reddit.router)
app.include_router(social.router)
app.include_router(sentiment.router)
app.include_router(sectors.router)
app.include_router(market_movers.router)
