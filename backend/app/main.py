from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import (
    auth,
    holdings,
    tickers,
    user,
    yahoo_finance,
    sectors,
    market_movers,
    ai_agents,
    suggestions,
)
from app.routes import graph
from app.database_graph import create_constraints, close_driver
from app.services.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    await create_constraints()
    await start_scheduler()
    yield
    await stop_scheduler()
    await close_driver()


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
app.include_router(yahoo_finance.router)
app.include_router(sectors.router)
app.include_router(market_movers.router)
app.include_router(graph.router)
app.include_router(ai_agents.router)
app.include_router(suggestions.router)
