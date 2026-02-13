"""Tests for dashboard API endpoints."""
import pytest
from httpx import AsyncClient
from app.models import Mention


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
