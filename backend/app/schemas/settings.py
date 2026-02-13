from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


class TranscriptionSettingsResponse(BaseModel):
    provider: Literal["local", "external"]
    external_url: str
    model: str
    has_external_api_key: bool


class TranscriptionSettingsUpdate(BaseModel):
    provider: Literal["local", "external"]
    external_url: HttpUrl
    model: str = Field(min_length=1, max_length=200)
    external_api_key: str | None = None
    clear_external_api_key: bool = False
