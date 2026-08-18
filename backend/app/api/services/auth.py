from datetime import datetime, timezone
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.models import Item, User
from app.api.schemas import AuthResponse, ItemCreate, ItemUpdate, SigninInput, SignupInput
from app.infra.security import create_access_token, hash_password, verify_password
 
# READ ONE
async def user_exist(session: AsyncSession, email: str) -> bool:
    try:

        result = await session.execute(
            select(User).where(User.email == email)
        )
        user =  result.scalar_one_or_none() 
    except Exception as e:
        return f"Query Error : {str(e)}"
 
# CREATE
async def create_user(session: AsyncSession, payload: SignupInput) -> AuthResponse:

    try: 
        exist  = await user_exist(session, payload.email)

        if exist:
            raise Exception("Email already existed.")
        
        hased_password = hash_password(payload.password)

        user = User( 
            name=payload.name,
            email=payload.email,
            password_hash=hased_password
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user
    
    except:
        raise Exception("Something went wrong")


async def signin(session: AsyncSession, payload: SigninInput) -> AuthResponse:

    
    result = await session.execute(
        select(User).where(User.email == payload.email)
    )
    user = result.scalar_one_or_none()  

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    access_token = create_access_token(user_id=str(user.id))

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user,
    } 
