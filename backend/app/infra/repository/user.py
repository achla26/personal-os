from uuid import UUID
from sqlalchemy import select 
from app.infra.models import User

async def create(session, user: User) -> User:
    session.add(user)
    await session.flush()
    await session.refresh(user)
    return user

# READ ALL
async def list(
    session,
    user_id: UUID,
    user_type: str | None = None,
    status: str | None = None,
    limit: int = 50,
) -> list[User]:
    
    stmt = select(User).where(User.user_id == user_id)

    if user_type:
        stmt = stmt.where(User.user_type == user_type)

    if status:
        stmt = stmt.where(User.status == status)

    stmt = stmt.order_by(User.created_at.desc()).limit(limit)

    result = await session.execute(stmt)

    return result.scalars().all()

async def get(session, user_id: UUID) -> User | None:
    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalar_one_or_none()


async def get_by_email(session, email: str) -> User | None:
    result = await session.execute(
        select(User).where(User.email == email)
    )
    return result.scalar_one_or_none()

async def update(session, user: User, data: dict) -> User:
    for key, value in data.users():
        setattr(user, key, value)
    await session.flush()
    await session.refresh(user)
    return user

async def delete(session, user: User) -> None:
    await session.delete(user)
    await session.flush()