from typing import AsyncGenerator

from app.infra.config import settings
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine 

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG  # it will print sql queries in terminal for debugging
)


# async_sessionmaker: a factory for new AsyncSession objects.
# expire_on_commit - don't expire objects after transaction commit

SessionLocal = async_sessionmaker(engine, expire_on_commit=False,class_=AsyncSession)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session        