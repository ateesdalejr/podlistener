from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.database import get_db
from app.models import Mention, Episode, Feed, Keyword
from app.schemas.mentions import MentionResponse

router = APIRouter(prefix="/mentions", tags=["mentions"])


@router.get("", response_model=list[MentionResponse])
async def list_mentions(
    feed_id: Optional[UUID] = Query(None),
    keyword_id: Optional[UUID] = Query(None),
    sentiment: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Mention)
        .join(Episode)
        .join(Feed, Episode.feed_id == Feed.id)
        .join(Keyword)
        .options(joinedload(Mention.episode).joinedload(Episode.feed), joinedload(Mention.keyword))
        .order_by(Mention.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    if feed_id:
        query = query.where(Episode.feed_id == feed_id)
    if keyword_id:
        query = query.where(Mention.keyword_id == keyword_id)
    if sentiment:
        query = query.where(Mention.sentiment == sentiment)

    result = await db.execute(query)
    mentions = []
    for m in result.unique().scalars().all():
        resp = MentionResponse.model_validate(m)
        resp.episode_title = m.episode.title
        resp.podcast_title = m.episode.feed.title
        resp.keyword_phrase = m.keyword.phrase
        return_topics = m.topics if isinstance(m.topics, list) else []
        resp.topics = return_topics
        mentions.append(resp)
    return mentions


@router.get("/{mention_id}", response_model=MentionResponse)
async def get_mention(mention_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Mention)
        .where(Mention.id == mention_id)
        .options(joinedload(Mention.episode).joinedload(Episode.feed), joinedload(Mention.keyword))
    )
    m = result.unique().scalar_one_or_none()
    if not m:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Mention not found")
    resp = MentionResponse.model_validate(m)
    resp.episode_title = m.episode.title
    resp.podcast_title = m.episode.feed.title
    resp.keyword_phrase = m.keyword.phrase
    resp.topics = m.topics if isinstance(m.topics, list) else []
    return resp
