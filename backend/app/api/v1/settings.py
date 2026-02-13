from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.settings import TranscriptionSettingsResponse, TranscriptionSettingsUpdate
from app.services.transcription_runtime_config import (
    get_transcription_config_async,
    update_transcription_config_async,
)

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/transcription", response_model=TranscriptionSettingsResponse)
async def get_transcription_settings(db: AsyncSession = Depends(get_db)):
    config = await get_transcription_config_async(db)
    return TranscriptionSettingsResponse(
        provider=config["provider"],
        external_url=config["external_url"],
        model=config["model"],
        has_external_api_key=bool(config["external_api_key"]),
    )


@router.put("/transcription", response_model=TranscriptionSettingsResponse)
async def update_transcription_settings(
    payload: TranscriptionSettingsUpdate,
    db: AsyncSession = Depends(get_db),
):
    await update_transcription_config_async(
        db,
        provider=payload.provider,
        external_url=str(payload.external_url),
        model=payload.model,
        external_api_key=payload.external_api_key,
        clear_external_api_key=payload.clear_external_api_key,
    )
    config = await get_transcription_config_async(db)
    return TranscriptionSettingsResponse(
        provider=config["provider"],
        external_url=config["external_url"],
        model=config["model"],
        has_external_api_key=bool(config["external_api_key"]),
    )
