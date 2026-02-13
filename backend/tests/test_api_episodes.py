"""Tests for episode API endpoints."""
import pytest
from httpx import AsyncClient
from app.models import Feed, Episode


@pytest.mark.asyncio
async def test_list_episodes_by_feed(client: AsyncClient, sample_feed: Feed, sample_episode: Episode):
    resp = await client.get(f"/api/v1/episodes/by-feed/{sample_feed.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["title"] == "Test Episode"
    assert data[0]["status"] == "completed"


@pytest.mark.asyncio
async def test_list_episodes_empty_feed(client: AsyncClient, sample_feed: Feed):
    # sample_feed has no episodes in this test (no sample_episode fixture)
    resp = await client.get(f"/api/v1/episodes/by-feed/{sample_feed.id}")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_get_episode_detail(client: AsyncClient, sample_episode: Episode):
    resp = await client.get(f"/api/v1/episodes/{sample_episode.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Test Episode"
    assert data["transcript_text"] is not None


@pytest.mark.asyncio
async def test_get_episode_not_found(client: AsyncClient):
    resp = await client.get("/api/v1/episodes/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404
