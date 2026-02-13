from datetime import datetime
from uuid import UUID
from typing import Optional

from pydantic import BaseModel


class MentionResponse(BaseModel):
    id: UUID
    episode_id: UUID
    keyword_id: UUID
    matched_text: str
    transcript_segment: str
    sentiment: Optional[str]
    sentiment_score: Optional[float]
    context_summary: Optional[str]
    topics: Optional[list]
    is_buying_signal: Optional[bool]
    is_pain_point: Optional[bool]
    is_recommendation: Optional[bool]
    created_at: datetime

    # Joined fields
    episode_title: Optional[str] = None
    podcast_title: Optional[str] = None
    keyword_phrase: Optional[str] = None

    model_config = {"from_attributes": True}
