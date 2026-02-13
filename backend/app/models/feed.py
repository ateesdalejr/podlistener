from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin, TimestampMixin


class Feed(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "feeds"

    rss_url: Mapped[str] = mapped_column(String, unique=True)
    title: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    last_polled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    episodes: Mapped[list["Episode"]] = relationship(back_populates="feed", cascade="all, delete-orphan")
