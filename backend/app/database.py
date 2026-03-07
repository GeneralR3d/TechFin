from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from collections.abc import AsyncGenerator

from app.config import settings

# Use psycopg (v3) async driver; plain postgresql:// defaults to psycopg2 (sync)
url = settings.DATABASE_URL
if url.startswith("postgresql://") and "+psycopg" not in url:
    url = url.replace("postgresql://", "postgresql+psycopg://", 1)

# psycopg does not support "pgbouncer" or "connection_limit"; strip them from the URL.
# psycopg also does not support sslmode=no-verify; use "require" (Supabase has valid TLS).
parsed = urlparse(url)
if parsed.query:
    params = parse_qs(parsed.query, keep_blank_values=True)
    for key in ("pgbouncer", "connection_limit"):
        params.pop(key, None)
    if params.get("sslmode") == ["no-verify"]:
        params["sslmode"] = ["require"]
    new_query = urlencode(params, doseq=True)
    url = urlunparse(parsed._replace(query=new_query))

engine = create_async_engine(url, echo=False)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
