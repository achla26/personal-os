from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.db import get_db
from app.api.deps import get_current_user
from app.api.schemas import ItemCreate, ItemUpdate, ItemRead
from app.infra.models import User

from app.api.services.items import (
    list_items,
    get_item,
    create_item,
    update_item,
    delete_item,
)

router = APIRouter(prefix="/items", tags=["items"])


# GET ALL
@router.get("/", response_model=list[ItemRead])
async def fetch_all_items(
    item_type: str | None = None,
    status: str | None = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await list_items(
        session=db,
        user_id=current_user.id,
        item_type=item_type,
        status=status,
        limit=limit,
    )


# GET ONE
@router.get("/{item_id}", response_model=ItemRead)
async def fetch_item(
    item_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await get_item(
        session=db,
        user_id=current_user.id,
        item_id=item_id,
    )


# CREATE
@router.post("/", response_model=ItemRead, status_code=status.HTTP_201_CREATED)
async def add_item(
    payload: ItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await create_item(
        session=db,
        user_id=current_user.id,
        payload=payload,
    )


# UPDATE
@router.patch("/{item_id}", response_model=ItemRead)
async def patch_item(
    item_id: UUID,
    payload: ItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await update_item(
        session=db,
        user_id=current_user.id,
        item_id=item_id,
        payload=payload,
    )


# DELETE
@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_item(
    item_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await delete_item(
        session=db,
        user_id=current_user.id,
        item_id=item_id,
    )
    return None