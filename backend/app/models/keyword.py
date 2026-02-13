from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin, TimestampMixin


class Keyword(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "keywords"

    phrase: Mapped[str] = mapped_column(String, unique=True)
    match_type: Mapped[str] = mapped_column(String, default="contains")
    # contains | exact_word | regex

    mentions: Mapped[list["Mention"]] = relationship(back_populates="keyword", cascade="all, delete-orphan")
