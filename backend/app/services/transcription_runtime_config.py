from typing import Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import SyncSessionLocal
from app.models import AppSetting

Provider = Literal["local", "external"]

TRANSCRIPTION_PROVIDER_KEY = "transcription.provider"
TRANSCRIPTION_EXTERNAL_URL_KEY = "transcription.external_url"
TRANSCRIPTION_EXTERNAL_API_KEY = "transcription.external_api_key"
TRANSCRIPTION_MODEL_KEY = "transcription.model"

TRANSCRIPTION_SETTING_KEYS = (
    TRANSCRIPTION_PROVIDER_KEY,
    TRANSCRIPTION_EXTERNAL_URL_KEY,
    TRANSCRIPTION_EXTERNAL_API_KEY,
    TRANSCRIPTION_MODEL_KEY,
)


def _normalize_provider(provider: str | None) -> Provider:
    if provider in ("cloud", "external"):
        return "external"
    return "local"


def _default_external_url() -> str:
    return f"{settings.CLOUD_TRANSCRIPTION_BASE_URL.rstrip('/')}/audio/transcriptions"


def _resolved_config(stored: dict[str, str | None]) -> dict[str, str]:
    provider = _normalize_provider(stored.get(TRANSCRIPTION_PROVIDER_KEY, settings.TRANSCRIPTION_PROVIDER))
    external_url = stored.get(TRANSCRIPTION_EXTERNAL_URL_KEY) or _default_external_url()
    if TRANSCRIPTION_EXTERNAL_API_KEY in stored:
        external_api_key = stored.get(TRANSCRIPTION_EXTERNAL_API_KEY) or ""
    else:
        external_api_key = settings.CLOUD_TRANSCRIPTION_API_KEY
    model = stored.get(TRANSCRIPTION_MODEL_KEY) or settings.TRANSCRIPTION_MODEL
    return {
        "provider": provider,
        "external_url": external_url,
        "external_api_key": external_api_key,
        "model": model,
    }


def _upsert_settings(rows: dict[str, str], existing: dict[str, AppSetting]) -> None:
    for key, value in rows.items():
        row = existing.get(key)
        if row:
            row.value = value
        else:
            existing[key] = AppSetting(key=key, value=value)


def get_transcription_config_sync() -> dict[str, str]:
    with SyncSessionLocal() as db:
        result = db.execute(select(AppSetting).where(AppSetting.key.in_(TRANSCRIPTION_SETTING_KEYS)))
        rows = result.scalars().all()
        stored = {row.key: row.value for row in rows}
        return _resolved_config(stored)


async def get_transcription_config_async(db: AsyncSession) -> dict[str, str]:
    result = await db.execute(select(AppSetting).where(AppSetting.key.in_(TRANSCRIPTION_SETTING_KEYS)))
    rows = result.scalars().all()
    stored = {row.key: row.value for row in rows}
    return _resolved_config(stored)


async def update_transcription_config_async(
    db: AsyncSession,
    *,
    provider: Provider,
    external_url: str,
    model: str,
    external_api_key: str | None = None,
    clear_external_api_key: bool = False,
) -> None:
    result = await db.execute(select(AppSetting).where(AppSetting.key.in_(TRANSCRIPTION_SETTING_KEYS)))
    rows = result.scalars().all()
    existing = {row.key: row for row in rows}

    to_write = {
        TRANSCRIPTION_PROVIDER_KEY: provider,
        TRANSCRIPTION_EXTERNAL_URL_KEY: external_url,
        TRANSCRIPTION_MODEL_KEY: model,
    }
    _upsert_settings(to_write, existing)

    if clear_external_api_key:
        _upsert_settings({TRANSCRIPTION_EXTERNAL_API_KEY: ""}, existing)
    elif external_api_key is not None:
        _upsert_settings({TRANSCRIPTION_EXTERNAL_API_KEY: external_api_key}, existing)

    for row in existing.values():
        db.add(row)
    await db.commit()
