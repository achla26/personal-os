from fastapi import APIRouter, Depends, HTTPException, Request, Response, status 

from app.api.schemas import AuthResponse, SigninInput, SignupInput, UserRead

from sqlalchemy.ext.asyncio import AsyncSession
from app.infra.db import get_db
from app.api.services.auth import create_user, issue_refresh_token, refresh_access_token, signin
from app.infra.security import create_access_token
from app.infra.core.errors import UnauthorizedError

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=AuthResponse)
async def login(
    payload: SigninInput,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    # 1. Verify credentials
    user = await signin(session=db, payload=payload)

   # 2. Create access token
    access_token = create_access_token(user_id=str(user.id))

    # 3. Issue refresh token
    refresh_cookie = await issue_refresh_token(session=db, user_id=user.id)
    await db.commit()  # commit - access + refresh both

    response.set_cookie(
        key="refresh_token",
        value=refresh_cookie,
        httponly=True,
        secure=False,   # TODO: local in dev  False, in prod True
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
    )

    return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user
        }


@router.post("/sign-up", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(
    payload: SignupInput,
    db: AsyncSession = Depends(get_db)
):
    return await create_user(session=db, payload=payload)

@router.post("/logout")
async def logout():
    pass

@router.post("/refresh")
async def refresh(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    cookie_value = request.cookies.get("refresh_token")

    if not cookie_value:
        raise UnauthorizedError("Missing refresh token")

    return await refresh_access_token(session=db, cookie_value=cookie_value)

