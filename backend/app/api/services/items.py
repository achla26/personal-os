from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.models.item import Item 
from app.api.schemas import ItemCreate, ItemUpdate
import app.infra.repository.item as items_repo


async def create_item(
    session: AsyncSession,
    user_id: UUID,
    payload: ItemCreate,
) -> Item:
    item = Item(
        user_id=user_id,
        title=payload.title,
        item_type=payload.item_type,
        body=payload.body,
        nag_policy=payload.nag_policy or "off",
    )
    item = await items_repo.create(session, item)
    await session.commit()
    return item


async def update_item(
    session: AsyncSession,
    user_id: UUID,
    item_id: UUID,
    payload: ItemUpdate,
) -> Item:
    item = await items_repo.get(session, user_id, item_id)

    if item is None:
        raise Exception("Item not found")

    data = payload.model_dump(exclude_unset=True)

    if data.get("status") == "done":
        data["completed_at"] = datetime.now(timezone.utc)
        data["next_nag_at"] = None

    item = await items_repo.update(session, item, data)
    await session.commit()
    return item


async def list_items(
    session: AsyncSession,
    user_id: UUID,
    item_type: str | None = None,
    status: str | None = None,
    limit: int = 50,
) -> list[Item]:
    return await items_repo.list(
        session,
        user_id=user_id,
        item_type=item_type,
        status=status,
        limit=limit,
    )


async def get_item(
    session: AsyncSession,
    user_id: UUID,
    item_id: UUID,
) -> Item:
    item = await items_repo.get(session, user_id=user_id, item_id=item_id)

    if item is None:
        raise Exception("Item not found")

    return item


async def delete_item(
    session: AsyncSession,
    user_id: UUID,
    item_id: UUID,
) -> None:
    item = await items_repo.get(session, user_id=user_id, item_id=item_id)

    if item is None:
        raise Exception("Item not found")

    await items_repo.delete(session, item)
    await session.commit()