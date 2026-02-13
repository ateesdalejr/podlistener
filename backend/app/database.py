from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from app.config import settings

async_engine = create_async_engine(settings.DATABASE_URL)
AsyncSessionLocal = async_sessionmaker(async_engine, expire_on_commit=False)

sync_engine = create_engine(settings.DATABASE_URL_SYNC)
SyncSessionLocal = sessionmaker(sync_engine)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
