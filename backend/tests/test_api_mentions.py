"""Tests for mention API endpoints."""
import pytest
from httpx import AsyncClient
from app.models import Mention


@pytest.mark.asyncio
async def test_list_mentions_empty(client: AsyncClient):
    resp = await client.get("/api/v1/mentions")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_list_mentions_with_data(client: AsyncClient, sample_mention: Mention):
    resp = await client.get("/api/v1/mentions")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["sentiment"] == "positive"
    assert data[0]["keyword_phrase"] == "Acme Corp"
    assert data[0]["podcast_title"] == "Test Podcast"


@pytest.mark.asyncio
async def test_list_mentions_filter_sentiment(client: AsyncClient, sample_mention: Mention):
    resp = await client.get("/api/v1/mentions?sentiment=positive")
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp = await client.get("/api/v1/mentions?sentiment=negative")
    assert resp.status_code == 200
    assert len(resp.json()) == 0


@pytest.mark.asyncio
async def test_get_mention_detail(client: AsyncClient, sample_mention: Mention):
    resp = await client.get(f"/api/v1/mentions/{sample_mention.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["context_summary"] == "Speaker endorses Acme Corp's platform"
    assert data["is_recommendation"] is True


@pytest.mark.asyncio
async def test_get_mention_not_found(client: AsyncClient):
    resp = await client.get("/api/v1/mentions/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404
