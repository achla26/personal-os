from fastapi import HTTPException, status, Depends
from sqlalchemy import select

from app.infra.models import User
from app.infra.config import settings
from app.infra.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession

async def get_current_user( session: AsyncSession = Depends(get_db),) -> User:
    # TODO session 5: JWT 
    try:
        user_id = settings.DEV_USER_ID
    
        result = await session.execute(
            select(User).where(User.id == user_id)
        )

        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="User not found"
            )

        return user

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail=f"Auth error: {str(e)}"
        )