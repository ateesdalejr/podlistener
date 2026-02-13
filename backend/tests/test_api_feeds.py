"""Tests for feed API endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_feeds_empty(client: AsyncClient):
    resp = await client.get("/api/v1/feeds")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_create_feed(client: AsyncClient):
    resp = await client.post(
        "/api/v1/feeds",
        json={"rss_url": "https://example.com/podcast.xml"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["rss_url"] == "https://example.com/podcast.xml"
    assert data["id"] is not None


@pytest.mark.asyncio
async def test_create_duplicate_feed(client: AsyncClient):
    await client.post(
        "/api/v1/feeds",
        json={"rss_url": "https://example.com/podcast.xml"},
    )
    resp = await client.post(
        "/api/v1/feeds",
        json={"rss_url": "https://example.com/podcast.xml"},
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_create_feed_invalid_url(client: AsyncClient):
    resp = await client.post(
        "/api/v1/feeds",
        json={"rss_url": "not-a-url"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_delete_feed(client: AsyncClient):
    create_resp = await client.post(
        "/api/v1/feeds",
        json={"rss_url": "https://example.com/podcast.xml"},
    )
    feed_id = create_resp.json()["id"]

    resp = await client.delete(f"/api/v1/feeds/{feed_id}")
    assert resp.status_code == 204

    list_resp = await client.get("/api/v1/feeds")
    assert list_resp.json() == []


@pytest.mark.asyncio
async def test_delete_feed_not_found(client: AsyncClient):
    resp = await client.delete("/api/v1/feeds/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_feeds_after_create(client: AsyncClient):
    await client.post(
        "/api/v1/feeds",
        json={"rss_url": "https://example.com/feed1.xml"},
    )
    await client.post(
        "/api/v1/feeds",
        json={"rss_url": "https://example.com/feed2.xml"},
    )
    resp = await client.get("/api/v1/feeds")
    assert resp.status_code == 200
    assert len(resp.json()) == 2
