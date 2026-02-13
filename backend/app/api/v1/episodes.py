from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Episode, Mention
from app.schemas.episodes import EpisodeResponse, EpisodeDetailResponse

router = APIRouter(prefix="/episodes", tags=["episodes"])


@router.get("/by-feed/{feed_id}", response_model=list[EpisodeResponse])
async def list_episodes_by_feed(feed_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(
            Episode,
            func.count(Mention.id).label("mention_count"),
        )
        .outerjoin(Mention)
        .where(Episode.feed_id == feed_id)
        .group_by(Episode.id)
        .order_by(Episode.published_at.desc().nullslast())
    )
    episodes = []
    for ep, count in result.all():
        resp = EpisodeResponse.model_validate(ep)
        resp.mention_count = count
        episodes.append(resp)
    return episodes


@router.get("/{episode_id}", response_model=EpisodeDetailResponse)
async def get_episode(episode_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Episode).where(Episode.id == episode_id))
    episode = result.scalar_one_or_none()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    return EpisodeDetailResponse.model_validate(episode)


@router.post("/{episode_id}/reprocess", status_code=202)
async def reprocess_episode(episode_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Episode).where(Episode.id == episode_id))
    episode = result.scalar_one_or_none()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    episode.status = "pending"
    episode.error_message = None
    await db.commit()

    from app.worker.tasks.process import process_episode
    process_episode.delay(str(episode_id))

    return {"status": "reprocessing", "episode_id": str(episode_id)}


@router.post("/{episode_id}/retry-enrichment", status_code=202)
async def retry_episode_enrichment(episode_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Episode).where(Episode.id == episode_id))
    episode = result.scalar_one_or_none()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    if not episode.transcript_text:
        raise HTTPException(status_code=409, detail="Cannot retry enrichment without transcript")

    episode.status = "analyzing"
    episode.error_message = None
    await db.commit()

    from app.worker.tasks.process import detect_episode_keywords

    detect_episode_keywords.delay({"episode_id": str(episode_id), "transcription_done": True})
    return {"status": "retrying_enrichment", "episode_id": str(episode_id)}
