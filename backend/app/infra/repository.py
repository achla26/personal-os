from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.models import Item
from app.api.schemas import ItemCreate, ItemUpdate


# CREATE
async def add_item(session: AsyncSession, user_id: UUID, payload: ItemCreate) -> Item:
    item = Item(
        user_id=user_id,
        title=payload.title,
        item_type=payload.item_type,
        body=payload.body,
        nag_policy=payload.nag_policy or "off",
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


# READ ALL
async def get_items(session: AsyncSession, user_id: UUID, item_type: str|None , status: str|None ,limit) -> list[Item]:
    stmt =  select(Item).where(Item.user_id == user_id)
    
    if item_type is not None:
        stmt = stmt.where(Item.item_type == item_type)

    if status is not None:
        stmt = stmt.where(Item.status == status)    

    stmt = stmt.order_by(Item.created_at.desc()).limit(limit)

    result = await session.execute(stmt)
    return result.scalars().all() 

# READ ONE
async def get_item_by_id(session: AsyncSession, user_id: UUID, item_id: UUID) -> Item | None:
    result = await session.execute(
        select(Item).where(
            Item.id == item_id,
            Item.user_id == user_id,  
        )
    )
    return result.scalar_one_or_none()


# UPDATE
async def update_item(
    session: AsyncSession,
    item: Item,
    payload: ItemUpdate,
) -> Item: 
    update_data = payload.model_dump(exclude_unset=True)

    
    if update_data.get("status") == "done":
        update_data["completed_at"] = datetime.now(timezone.utc)
        update_data["next_nag_at"] = None

    for key, value in update_data.items():
        setattr(item, key, value)

    await session.commit()
    await session.refresh(item)
    return item


# DELETE
async def delete_item(session: AsyncSession, item: Item) -> None:
    await session.delete(item)
    await session.commit()