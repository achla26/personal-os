from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.models import RefreshToken


async def create(
        session: AsyncSession, 
        token: RefreshToken
    ) -> RefreshToken:

    session.add(token)
    await session.flush()
    await session.refresh(token)
    return token


async def get_by_id(
        session: AsyncSession,
        token_id: UUID
    ) -> RefreshToken | None:

    result = await session.execute(
        select(RefreshToken).where(RefreshToken.id == token_id)
    )
    return result.scalar_one_or_none()



async def revoke(
    session: AsyncSession, 
    token: RefreshToken
) -> None:
    token.revoked_at = datetime.now(timezone.utc)
    await session.flush()