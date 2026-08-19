import secrets
import uuid
from datetime import datetime, timedelta, timezone 
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.models import  User, RefreshToken
from app.api.schemas import AuthResponse, SigninInput, SignupInput, UserRead
from app.infra.security import create_access_token, hash_password, verify_password

import app.infra.repository.user as user_repo
import app.infra.repository.refresh_token as refresh_repo

from app.infra.core.errors import (
    ConflictError,
    UnauthorizedError,
)

# CREATE
async def create_user(
    session: AsyncSession,
    payload: SignupInput,
) -> User:
    existing = await user_repo.get_by_email(session, payload.email)

    if existing is not None:
        raise ConflictError("Email already exists")

    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
    )

    user = await user_repo.create(session, user)
    await session.commit()
    return user

async def signin(session: AsyncSession, payload: SigninInput) -> UserRead:
    user = await user_repo.get_by_email(session, payload.email)

    if user is None:
            raise UnauthorizedError("Invalid credentials")
    
    if not verify_password(payload.password, user.password_hash):
        raise UnauthorizedError("Invalid credentials")

    return user


async def issue_refresh_token(
    session: AsyncSession,
    user_id: UUID,
) -> str:
    token_id = uuid.uuid4()
    secret = secrets.token_urlsafe(32)
    cookie_value = f"{token_id}.{secret}"

    refresh = RefreshToken(
        id=token_id,
        user_id=user_id,
        token_hash=hash_password(secret),
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )

    await refresh_repo.create(session, refresh)
    # commit yahan nahi — route me hoga

    return cookie_value

async def refresh_access_token(
    session: AsyncSession,
    cookie_value: str,
) -> tuple[dict, str]:
    # Parse cookie
    try:
        token_id_str, secret = cookie_value.split(".", 1)
        token_id = UUID(token_id_str)
        
    except (ValueError, AttributeError):
        raise UnauthorizedError("Invalid refresh token")

    # Get from DB
    old_refresh = await refresh_repo.get_by_id(session, token_id)

    if old_refresh is None:
        raise UnauthorizedError("Invalid refresh token")

    if old_refresh.revoked_at is not None:
        raise UnauthorizedError("Refresh token revoked")

    if old_refresh.expires_at <= datetime.now(timezone.utc):
        raise UnauthorizedError("Refresh token expired")

    if not verify_password(secret, old_refresh.token_hash):
        raise UnauthorizedError("Invalid refresh token")

    # ROTATION: revoke old + issue new
    await refresh_repo.revoke(session, old_refresh)
    new_cookie_value = await issue_refresh_token(session, old_refresh.user_id)

    # New access token
    access_token = create_access_token(user_id=str(old_refresh.user_id))

    return (
        {
            "access_token": access_token,
            "token_type": "bearer",
        },
        new_cookie_value,
    )