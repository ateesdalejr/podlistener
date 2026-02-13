"""Tests for dashboard API endpoints."""
import pytest
from httpx import AsyncClient
from datetime import datetime, timezone
import uuid

from app.models import Mention
from app.models import Episode


@pytest.mark.asyncio
async def test_dashboard_stats_empty(client: AsyncClient):
    resp = await client.get("/api/v1/dashboard/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["feeds"] == 0
    assert data["episodes"] == 0
    assert data["keywords"] == 0
    assert data["mentions"] == 0


@pytest.mark.asyncio
async def test_dashboard_stats_with_data(client: AsyncClient, sample_mention: Mention):
    resp = await client.get("/api/v1/dashboard/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["feeds"] == 1
    assert data["episodes"] == 1
    assert data["keywords"] == 1
    assert data["mentions"] == 1
    assert data["episodes_completed"] == 1


@pytest.mark.asyncio
async def test_dashboard_processing_excludes_pending(client: AsyncClient, db, sample_feed):
    pending_episode = Episode(
        id=uuid.uuid4(),
        feed_id=sample_feed.id,
        guid="pending-ep-001",
        title="Pending Episode",
        audio_url="https://example.com/pending.mp3",
        status="pending",
        published_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    transcribing_episode = Episode(
        id=uuid.uuid4(),
        feed_id=sample_feed.id,
        guid="transcribing-ep-001",
        title="Transcribing Episode",
        audio_url="https://example.com/transcribing.mp3",
        status="transcribing",
        published_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add_all([pending_episode, transcribing_episode])
    await db.commit()

    resp = await client.get("/api/v1/dashboard/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["episodes_processing"] == 1
