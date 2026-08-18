from fastapi import APIRouter, Depends, Response, status 

from app.api.schemas import AuthResponse, SigninInput, SignupInput, UserRead

from sqlalchemy.ext.asyncio import AsyncSession
from app.infra.db import get_db
from app.api.services.auth import create_user, signin

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=AuthResponse)
async def login(
    payload: SigninInput,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    user = await signin(session=db, payload=payload)

    response.headers["Authorization"] = f"Bearer {user['access_token']}"
    return user

@router.post("/sign-up",response_model=UserRead)
async def register(payload: SignupInput,
db: AsyncSession = Depends(get_db)):
    user = await create_user(session=db, payload=payload)
    return user
