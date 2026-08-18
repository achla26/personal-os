from fastapi import APIRouter, Depends, status 

from app.api.schemas import AuthResponse, SigninInput, SignupInput

from sqlalchemy.ext.asyncio import AsyncSession
from app.infra.db import get_db
from app.api.services.auth import create_user, signin

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login",response_model=AuthResponse)
async def login(payload: SigninInput, db: AsyncSession = Depends(get_db)):
    user = await signin(session=db, payload=payload)
    return user


@router.post("/sign-up",response_model=AuthResponse)
async def register(payload: SignupInput,
db: AsyncSession = Depends(get_db)):
    user = await create_user(session=db, payload=payload)
    return user
