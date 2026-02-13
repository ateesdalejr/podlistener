"""Tests for keyword API endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_keywords_empty(client: AsyncClient):
    resp = await client.get("/api/v1/keywords")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_create_keyword(client: AsyncClient):
    resp = await client.post(
        "/api/v1/keywords",
        json={"phrase": "Acme Corp", "match_type": "contains"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["phrase"] == "Acme Corp"
    assert data["match_type"] == "contains"


@pytest.mark.asyncio
async def test_create_keyword_default_match_type(client: AsyncClient):
    resp = await client.post(
        "/api/v1/keywords",
        json={"phrase": "test keyword"},
    )
    assert resp.status_code == 201
    assert resp.json()["match_type"] == "contains"


@pytest.mark.asyncio
async def test_create_keyword_exact_word(client: AsyncClient):
    resp = await client.post(
        "/api/v1/keywords",
        json={"phrase": "cloud", "match_type": "exact_word"},
    )
    assert resp.status_code == 201
    assert resp.json()["match_type"] == "exact_word"


@pytest.mark.asyncio
async def test_create_keyword_regex(client: AsyncClient):
    resp = await client.post(
        "/api/v1/keywords",
        json={"phrase": r"\btest\b", "match_type": "regex"},
    )
    assert resp.status_code == 201
    assert resp.json()["match_type"] == "regex"


@pytest.mark.asyncio
async def test_create_duplicate_keyword(client: AsyncClient):
    await client.post("/api/v1/keywords", json={"phrase": "dupe"})
    resp = await client.post("/api/v1/keywords", json={"phrase": "dupe"})
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_create_keyword_invalid_match_type(client: AsyncClient):
    resp = await client.post(
        "/api/v1/keywords",
        json={"phrase": "test", "match_type": "fuzzy"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_delete_keyword(client: AsyncClient):
    create_resp = await client.post(
        "/api/v1/keywords", json={"phrase": "deleteme"}
    )
    kw_id = create_resp.json()["id"]

    resp = await client.delete(f"/api/v1/keywords/{kw_id}")
    assert resp.status_code == 204

    list_resp = await client.get("/api/v1/keywords")
    assert len(list_resp.json()) == 0


@pytest.mark.asyncio
async def test_delete_keyword_not_found(client: AsyncClient):
    resp = await client.delete(
        "/api/v1/keywords/00000000-0000-0000-0000-000000000000"
    )
    assert resp.status_code == 404
