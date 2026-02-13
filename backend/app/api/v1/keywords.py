from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Keyword
from app.schemas.keywords import KeywordCreate, KeywordResponse

router = APIRouter(prefix="/keywords", tags=["keywords"])


@router.get("", response_model=list[KeywordResponse])
async def list_keywords(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Keyword).order_by(Keyword.created_at.desc()))
    return [KeywordResponse.model_validate(k) for k in result.scalars().all()]


@router.post("", response_model=KeywordResponse, status_code=201)
async def create_keyword(data: KeywordCreate, db: AsyncSession = Depends(get_db)):
    if data.match_type not in ("contains", "exact_word", "regex"):
        raise HTTPException(status_code=422, detail="match_type must be contains, exact_word, or regex")

    existing = await db.execute(select(Keyword).where(Keyword.phrase == data.phrase))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Keyword already exists")

    keyword = Keyword(phrase=data.phrase, match_type=data.match_type)
    db.add(keyword)
    await db.commit()
    await db.refresh(keyword)
    return KeywordResponse.model_validate(keyword)


@router.delete("/{keyword_id}", status_code=204)
async def delete_keyword(keyword_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Keyword).where(Keyword.id == keyword_id))
    keyword = result.scalar_one_or_none()
    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")
    await db.delete(keyword)
    await db.commit()
