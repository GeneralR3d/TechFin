"""add_sentiment_to_raw_news

Revision ID: b3c4d5e6f7a8
Revises: a1b2c3d4e5f6
Create Date: 2026-03-11 09:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op


revision: str = 'b3c4d5e6f7a8'
down_revision: Union[str, Sequence[str], None] = ('a1b2c3d4e5f6', 'e97709c06172')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('raw_news_articles', sa.Column('sentiment_score', sa.Float(), nullable=True))
    op.add_column('raw_news_articles', sa.Column('ticker_sentiment', postgresql.JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column('raw_news_articles', 'ticker_sentiment')
    op.drop_column('raw_news_articles', 'sentiment_score')
