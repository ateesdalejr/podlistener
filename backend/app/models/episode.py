import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin, TimestampMixin


class Episode(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "episodes"

    feed_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("feeds.id", ondelete="CASCADE"))
    guid: Mapped[str] = mapped_column(String, unique=True)
    title: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    audio_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String, default="pending")
    # pending → downloading → transcribing → analyzing → completed / failed
    transcript_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    feed: Mapped["Feed"] = relationship(back_populates="episodes")
    mentions: Mapped[list["Mention"]] = relationship(back_populates="episode", cascade="all, delete-orphan")
