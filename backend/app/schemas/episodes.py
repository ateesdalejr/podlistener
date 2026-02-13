from datetime import datetime
from uuid import UUID
from typing import Optional

from pydantic import BaseModel


class EpisodeResponse(BaseModel):
    id: UUID
    feed_id: UUID
    guid: str
    title: Optional[str]
    audio_url: Optional[str]
    published_at: Optional[datetime]
    status: str
    created_at: datetime
    mention_count: int = 0

    model_config = {"from_attributes": True}


class EpisodeDetailResponse(EpisodeResponse):
    transcript_text: Optional[str]
    error_message: Optional[str]
