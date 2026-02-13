import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Feed, Episode
from app.schemas.feeds import FeedCreate, FeedResponse

router = APIRouter(prefix="/feeds", tags=["feeds"])
logger = logging.getLogger(__name__)


@router.get("", response_model=list[FeedResponse])
async def list_feeds(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(
            Feed,
            func.count(Episode.id).label("episode_count"),
        )
        .outerjoin(Episode)
        .group_by(Feed.id)
        .order_by(Feed.created_at.desc())
    )
    feeds = []
    for feed, count in result.all():
        resp = FeedResponse.model_validate(feed)
        resp.episode_count = count
        feeds.append(resp)
    return feeds


@router.post("", response_model=FeedResponse, status_code=201)
async def create_feed(data: FeedCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(Feed).where(Feed.rss_url == str(data.rss_url)))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Feed already exists")

    feed = Feed(rss_url=str(data.rss_url))
    db.add(feed)
    await db.commit()
    await db.refresh(feed)

    # Kick off initial ingestion immediately instead of waiting for the 15-minute beat window.
    try:
        from app.worker.tasks.poll import poll_single_feed

        poll_single_feed.delay(str(feed.id))
    except Exception:
        logger.exception("Failed to enqueue initial poll for feed %s", feed.id)

    return FeedResponse.model_validate(feed)


@router.delete("/{feed_id}", status_code=204)
async def delete_feed(feed_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Feed).where(Feed.id == feed_id))
    feed = result.scalar_one_or_none()
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")
    await db.delete(feed)
    await db.commit()
