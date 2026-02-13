import os
import uuid
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker
from httpx import ASGITransport, AsyncClient

from app.models import Base, Feed, Episode, Keyword, Mention

# Use SQLite for tests
TEST_DB_URL = "sqlite+aiosqlite:///test.db"
TEST_DB_URL_SYNC = "sqlite:///test.db"

os.environ["DATABASE_URL"] = TEST_DB_URL
os.environ["DATABASE_URL_SYNC"] = TEST_DB_URL_SYNC
os.environ["REDIS_URL"] = "redis://localhost:6379/15"
os.environ["WHISPER_API_URL"] = "http://localhost:9000"
os.environ["OLLAMA_BASE_URL"] = "http://localhost:11434"

test_async_engine = create_async_engine(TEST_DB_URL, echo=False)
TestAsyncSession = async_sessionmaker(test_async_engine, expire_on_commit=False)

test_sync_engine = create_engine(TEST_DB_URL_SYNC)
TestSyncSession = sessionmaker(test_sync_engine)


@pytest_asyncio.fixture
async def db():
    async with test_async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestAsyncSession() as session:
        yield session

    async with test_async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client(db):
    from app.main import app
    from app.database import get_db

    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def sample_feed(db: AsyncSession) -> Feed:
    feed = Feed(
        id=uuid.uuid4(),
        rss_url="https://example.com/feed.xml",
        title="Test Podcast",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(feed)
    await db.commit()
    await db.refresh(feed)
    return feed


@pytest_asyncio.fixture
async def sample_episode(db: AsyncSession, sample_feed: Feed) -> Episode:
    episode = Episode(
        id=uuid.uuid4(),
        feed_id=sample_feed.id,
        guid="ep-001",
        title="Test Episode",
        audio_url="https://example.com/audio.mp3",
        status="completed",
        transcript_text="I've been using Acme Corp for six months and it's been great. Their customer support is amazing.",
        published_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(episode)
    await db.commit()
    await db.refresh(episode)
    return episode


@pytest_asyncio.fixture
async def sample_keyword(db: AsyncSession) -> Keyword:
    keyword = Keyword(
        id=uuid.uuid4(),
        phrase="Acme Corp",
        match_type="contains",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(keyword)
    await db.commit()
    await db.refresh(keyword)
    return keyword


@pytest_asyncio.fixture
async def sample_mention(
    db: AsyncSession, sample_episode: Episode, sample_keyword: Keyword
) -> Mention:
    mention = Mention(
        id=uuid.uuid4(),
        episode_id=sample_episode.id,
        keyword_id=sample_keyword.id,
        matched_text="Acme Corp",
        transcript_segment="I've been using Acme Corp for six months and it's been great.",
        sentiment="positive",
        sentiment_score=0.85,
        context_summary="Speaker endorses Acme Corp's platform",
        topics=["SaaS", "productivity"],
        is_buying_signal=False,
        is_pain_point=False,
        is_recommendation=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(mention)
    await db.commit()
    await db.refresh(mention)
    return mention
