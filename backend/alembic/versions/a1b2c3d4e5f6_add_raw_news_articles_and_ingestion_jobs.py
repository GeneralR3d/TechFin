"""add_raw_news_articles_and_ingestion_jobs

Revision ID: a1b2c3d4e5f6
Revises: ed54ef4f5664
Create Date: 2026-03-07 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'ed54ef4f5664'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'raw_news_articles',
        sa.Column('news_id', sa.String(length=64), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('source', sa.String(length=64), nullable=False),
        sa.Column('platform', sa.String(length=64), nullable=False),
        sa.Column('ticker_hint', sa.String(length=20), nullable=True),
        sa.Column('raw_tags', postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column('graph_ingested', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('graph_ingested_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ingested_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('news_id'),
    )
    op.create_index(op.f('ix_raw_news_articles_news_id'), 'raw_news_articles', ['news_id'], unique=True)

    op.create_table(
        'ingestion_jobs',
        sa.Column('source', sa.String(length=64), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('articles_fetched', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('articles_new', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('articles_graph_ingested', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(length=16), nullable=False, server_default='running'),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('ingestion_jobs')
    op.drop_index(op.f('ix_raw_news_articles_news_id'), table_name='raw_news_articles')
    op.drop_table('raw_news_articles')
