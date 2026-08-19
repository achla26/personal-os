from uuid import UUID
from sqlalchemy import select 

from app.infra.models import Item 

async def create(session, item: Item) -> Item:
    session.add(item)
    await session.flush()
    await session.refresh(item)
    return item

# READ ALL
async def list(
    session,
    user_id: UUID,
    item_type: str | None = None,
    status: str | None = None,
    limit: int = 50,
) -> list[Item]:
    
    stmt = select(Item).where(Item.user_id == user_id)

    if item_type:
        stmt = stmt.where(Item.item_type == item_type)

    if status:
        stmt = stmt.where(Item.status == status)

    stmt = stmt.order_by(Item.created_at.desc()).limit(limit)

    result = await session.execute(stmt)

    return result.scalars().all()

async def get(session, user_id: UUID, item_id: UUID) -> Item | None:
    result = await session.execute(
        select(Item).where(Item.id == item_id, Item.user_id == user_id)
    )
    return result.scalar_one_or_none()

async def update(session, item: Item, data: dict) -> Item:
    for key, value in data.items():
        setattr(item, key, value)
    await session.flush()
    await session.refresh(item)
    return item

async def delete(session, item: Item) -> None:
    await session.delete(item)
    await session.flush()