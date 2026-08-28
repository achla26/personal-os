from datetime import datetime
from uuid import UUID
from zoneinfo import ZoneInfo
from sqlalchemy import select 

from app.infra.models import Item
from app.infra.core.time import CURRENT_TIMEZONE, now_local_tz 

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
    x_timezone: str| None  = None,
    group: str | None = None
) -> list[Item]:
    
    stmt = select(Item).where(Item.user_id == user_id)

    if item_type:
        stmt = stmt.where(Item.item_type == item_type)

    if status:
        stmt = stmt.where(Item.status == status)

    stmt = stmt.order_by(Item.created_at.desc()).limit(limit)

    result = await session.execute(stmt)

    items = result.scalars().all()

    if group == "now":
        try:
            tz = ZoneInfo(x_timezone)
        except:
            tz = CURRENT_TIMEZONE

        # User local time according "today"
        today = now_local_tz(tz).date()

        grouped = {
            "overdue": [],
            "today": [],
            "this_week": [],
            "someday": []
        }

        for item in items:
            if not item.due_at:
                grouped["someday"].append(item)
                continue

            item_date = item.due_at.astimezone(tz).date()

            if item_date < today:
                grouped["overdue"].append(item)
            elif item_date == today:
                grouped["today"].append(item)
            elif (item_date - today).days <= 7:
                grouped["this_week"].append(item)
            else:
                grouped["someday"].append(item)

        return grouped

    return items

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