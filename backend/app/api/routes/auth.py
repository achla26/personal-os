from fastapi import APIRouter, Depends, HTTPException, Request, Response, status 

from app.api.schemas import AuthResponse, SigninInput, SignupInput, UserRead

from sqlalchemy.ext.asyncio import AsyncSession
from app.infra.db import get_db
from app.api.services.auth import create_user, issue_refresh_token, logout_user, refresh_access_token, signin
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

@router.post("/refresh")
async def refresh(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    #  get refresh token from cookie 
    cookie_value = request.cookies.get("refresh_token")

    #  validate
    if not cookie_value:
        raise UnauthorizedError("Missing refresh token")

    # revoke old refresh token, new refresh token  

    access_data, new_cookie_value = await refresh_access_token(
        session=db,
        cookie_value=cookie_value,
    )
    await db.commit()  # rotation commit

    # new cookie set 
    response.set_cookie(
        key="refresh_token",
        value=new_cookie_value,
        httponly=True,
        secure=False,  # in prod True
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
    )

    return access_data

@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    cookie_value = request.cookies.get("refresh_token")

    if cookie_value:
        await logout_user(session=db, cookie_value=cookie_value)
        await db.commit()

    # Cookie clear 
    response.delete_cookie(key="refresh_token")

    return {"message": "Logged out successfully"}