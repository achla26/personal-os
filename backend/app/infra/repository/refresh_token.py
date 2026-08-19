from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, update
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


async def revoke_all_for_user (
    session: AsyncSession, 
    user_id: UUID
) -> None:
    now = datetime.now(timezone.utc)
    stmt = (
        update(RefreshToken)
        .where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
        )
        .values(revoked_at=now)
    )
    
    await session.execute(stmt)
    await session.flush()
