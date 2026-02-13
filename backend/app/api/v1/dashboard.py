from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Feed, Episode, Keyword, Mention

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    feeds = await db.execute(select(func.count(Feed.id)))
    episodes = await db.execute(select(func.count(Episode.id)))
    keywords = await db.execute(select(func.count(Keyword.id)))
    mentions = await db.execute(select(func.count(Mention.id)))
    completed = await db.execute(
        select(func.count(Episode.id)).where(Episode.status == "completed")
    )
    processing = await db.execute(
        select(func.count(Episode.id)).where(
            Episode.status.in_(["pending", "downloading", "transcribing", "analyzing"])
        )
    )
    failed = await db.execute(
        select(func.count(Episode.id)).where(Episode.status == "failed")
    )

    return {
        "feeds": feeds.scalar() or 0,
        "episodes": episodes.scalar() or 0,
        "keywords": keywords.scalar() or 0,
        "mentions": mentions.scalar() or 0,
        "episodes_completed": completed.scalar() or 0,
        "episodes_processing": processing.scalar() or 0,
        "episodes_failed": failed.scalar() or 0,
    }
