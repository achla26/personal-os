from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status 
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.db import get_db
from app.api.deps import get_current_user
from app.infra.repository import (
    get_items,
    get_item_by_id,
    add_item,
    update_item,
    delete_item,
)
from app.api.schemas import ItemCreate, ItemUpdate, ItemRead
from app.infra.models import User

router = APIRouter(prefix="/items", tags=["items"])

# GET ALL
@router.get("/",response_model=list[ItemRead])
async def fetch_items(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    item_type: str|None = None,
    status: str | None = None,
    limit: int = 50,
):
    items = await get_items(session=db, user_id=current_user.id, 
    item_type = item_type,
    status= status,
    limit=limit
    )
    return items

# GET ONE
@router.get("/{item_id}", response_model=ItemRead)
async def fetch_item(
    item_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = await get_item_by_id(
        session=db,
        user_id=current_user.id,
        item_id=item_id,
    )

    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )

    return item


# CREATE
@router.post("/", response_model=ItemRead, status_code=status.HTTP_201_CREATED)
async def create_item(
    payload: ItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return await add_item(
            session=db,
            user_id=current_user.id,
            payload=payload,
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Query error: {str(e)}"
        )


# UPDATE
@router.patch("/{item_id}", response_model=ItemRead)
async def patch_item(
    item_id: UUID,
    payload: ItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # first find item 
    item = await get_item_by_id(
        session=db,
        user_id=current_user.id,
        item_id=item_id,
    )

    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )

    # then update 
    return await update_item(
        session=db,
        item=item,
        payload=payload,
    )


# DELETE
@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_item(
    item_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = await get_item_by_id(
        session=db,
        user_id=current_user.id,
        item_id=item_id,
    )

    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )

    await delete_item(session=db, item=item)

    # 204 nothing return
    return None