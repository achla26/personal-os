import secrets
import uuid
from datetime import datetime, timedelta, timezone 
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.models import Item, User, RefreshToken
from app.api.schemas import AuthResponse, SigninInput, SignupInput, UserRead
from app.infra.security import create_access_token, hash_password, verify_password

# READ ONE
async def user_exist(session: AsyncSession, email: str) -> bool:
    result = await session.execute(
        select(User).where(User.email == email)
    )
    user =  result.scalar_one_or_none() 

    if user is None:
        return False

    return True 
 
# CREATE
async def create_user(session: AsyncSession, payload: SignupInput) -> UserRead:

    
    exist  = await user_exist(session, payload.email)
    

    if exist:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email Already Exists",
        )
    
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

async def issue_refresh_token(session: AsyncSession, user_id: UUID) -> str:
    token_id = uuid.uuid4()
    secret = secrets.token_urlsafe(32)

    cookie_value = f"{token_id}.{secret}"

    refresh = RefreshToken(
        id=token_id,
        user_id=user_id,
        token_hash=hash_password(secret),    
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )

    session.add(refresh)
    await session.commit()

    return cookie_value


async def refresh_access_token(session: AsyncSession, cookie_value: str) -> dict:
    try:
        token_id_str, secret = cookie_value.split(".", 1)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    result = await session.execute(
        select(RefreshToken).where(RefreshToken.id == UUID(token_id_str))
    )
    refresh = result.scalar_one_or_none()

    if refresh is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    if refresh.revoked_at is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token revoked",
        )

    if refresh.expires_at <= datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired",
        )

    if not verify_password(secret, refresh.token_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    access_token = create_access_token(user_id=str(refresh.user_id))

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }