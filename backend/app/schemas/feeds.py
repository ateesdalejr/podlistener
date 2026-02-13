from datetime import datetime
from uuid import UUID
from typing import Optional

from pydantic import BaseModel, HttpUrl


class FeedCreate(BaseModel):
    rss_url: HttpUrl


class FeedResponse(BaseModel):
    id: UUID
    rss_url: str
    title: Optional[str]
    image_url: Optional[str]
    last_polled_at: Optional[datetime]
    created_at: datetime
    episode_count: int = 0

    model_config = {"from_attributes": True}
