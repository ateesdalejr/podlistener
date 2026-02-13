"""Tests for settings API endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_transcription_settings_defaults(client: AsyncClient):
    resp = await client.get("/api/v1/settings/transcription")
    assert resp.status_code == 200
    data = resp.json()
    assert data["provider"] == "local"
    assert data["model"] == "Systran/faster-whisper-small"
    assert data["has_external_api_key"] is False


@pytest.mark.asyncio
async def test_update_transcription_settings(client: AsyncClient):
    update_resp = await client.put(
        "/api/v1/settings/transcription",
        json={
            "provider": "external",
            "external_url": "https://api.openai.com/v1/audio/transcriptions",
            "model": "gpt-4o-mini-transcribe",
            "external_api_key": "abc123",
        },
    )
    assert update_resp.status_code == 200
    updated = update_resp.json()
    assert updated["provider"] == "external"
    assert updated["external_url"] == "https://api.openai.com/v1/audio/transcriptions"
    assert updated["model"] == "gpt-4o-mini-transcribe"
    assert updated["has_external_api_key"] is True

    get_resp = await client.get("/api/v1/settings/transcription")
    assert get_resp.status_code == 200
    fetched = get_resp.json()
    assert fetched["provider"] == "external"
    assert fetched["has_external_api_key"] is True


@pytest.mark.asyncio
async def test_update_transcription_settings_can_clear_api_key(client: AsyncClient):
    await client.put(
        "/api/v1/settings/transcription",
        json={
            "provider": "external",
            "external_url": "https://api.openai.com/v1/audio/transcriptions",
            "model": "gpt-4o-mini-transcribe",
            "external_api_key": "abc123",
        },
    )

    clear_resp = await client.put(
        "/api/v1/settings/transcription",
        json={
            "provider": "external",
            "external_url": "https://api.openai.com/v1/audio/transcriptions",
            "model": "gpt-4o-mini-transcribe",
            "clear_external_api_key": True,
        },
    )
    assert clear_resp.status_code == 200
    cleared = clear_resp.json()
    assert cleared["has_external_api_key"] is False
