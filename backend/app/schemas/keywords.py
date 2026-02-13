from datetime import datetime
from uuid import UUID
from typing import Optional

from pydantic import BaseModel


class KeywordCreate(BaseModel):
    phrase: str
    match_type: str = "contains"  # contains | exact_word | regex


class KeywordResponse(BaseModel):
    id: UUID
    phrase: str
    match_type: str
    created_at: datetime

    model_config = {"from_attributes": True}
