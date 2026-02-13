import uuid
from typing import Optional

from sqlalchemy import String, Text, Float, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin, TimestampMixin


class Mention(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "mentions"

    episode_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("episodes.id", ondelete="CASCADE"))
    keyword_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("keywords.id", ondelete="CASCADE"))
    matched_text: Mapped[str] = mapped_column(String)
    transcript_segment: Mapped[str] = mapped_column(Text)

    # Enrichment fields (filled by Ollama)
    sentiment: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    sentiment_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    context_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    topics: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    is_buying_signal: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    is_pain_point: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    is_recommendation: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    raw_llm_response: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    episode: Mapped["Episode"] = relationship(back_populates="mentions")
    keyword: Mapped["Keyword"] = relationship(back_populates="mentions")
