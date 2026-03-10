import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class RawNewsArticle(Base):
    __tablename__ = "raw_news_articles"

    news_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    title: Mapped[str] = mapped_column(Text)
    url: Mapped[str] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    source: Mapped[str] = mapped_column(String(64))   # Either "alphavantage" or "Yahoo Finance"
    platform: Mapped[str] = mapped_column(String(64))
    ticker_hint: Mapped[str | None] = mapped_column(String(20), nullable=True)
    raw_tags: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    sentiment_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    ticker_sentiment: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    graph_ingested: Mapped[bool] = mapped_column(Boolean, default=False)
    graph_ingested_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
