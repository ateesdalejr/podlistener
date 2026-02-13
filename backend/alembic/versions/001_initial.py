"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-02-13
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "feeds",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("rss_url", sa.String, unique=True, nullable=False),
        sa.Column("title", sa.String, nullable=True),
        sa.Column("image_url", sa.String, nullable=True),
        sa.Column("last_polled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "episodes",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("feed_id", UUID(as_uuid=True), sa.ForeignKey("feeds.id", ondelete="CASCADE"), nullable=False),
        sa.Column("guid", sa.String, unique=True, nullable=False),
        sa.Column("title", sa.String, nullable=True),
        sa.Column("audio_url", sa.String, nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String, nullable=False, server_default="pending"),
        sa.Column("transcript_text", sa.Text, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "keywords",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("phrase", sa.String, unique=True, nullable=False),
        sa.Column("match_type", sa.String, nullable=False, server_default="contains"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "mentions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("episode_id", UUID(as_uuid=True), sa.ForeignKey("episodes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("keyword_id", UUID(as_uuid=True), sa.ForeignKey("keywords.id", ondelete="CASCADE"), nullable=False),
        sa.Column("matched_text", sa.String, nullable=False),
        sa.Column("transcript_segment", sa.Text, nullable=False),
        sa.Column("sentiment", sa.String, nullable=True),
        sa.Column("sentiment_score", sa.Float, nullable=True),
        sa.Column("context_summary", sa.Text, nullable=True),
        sa.Column("topics", JSONB, nullable=True),
        sa.Column("is_buying_signal", sa.Boolean, nullable=True),
        sa.Column("is_pain_point", sa.Boolean, nullable=True),
        sa.Column("is_recommendation", sa.Boolean, nullable=True),
        sa.Column("raw_llm_response", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_index("ix_episodes_feed_id", "episodes", ["feed_id"])
    op.create_index("ix_mentions_episode_id", "mentions", ["episode_id"])
    op.create_index("ix_mentions_keyword_id", "mentions", ["keyword_id"])


def downgrade() -> None:
    op.drop_table("mentions")
    op.drop_table("keywords")
    op.drop_table("episodes")
    op.drop_table("feeds")
