from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.db import get_db
 
from app.api.routes.items import router as items_router
from app.api.routes.auth import router as auth_router
from app.api.deps import get_current_user
from app.api.schemas import UserRead
from app.infra.core.error_handlers import register_exception_handlers

app = FastAPI()

register_exception_handlers(app)

@app.get("/health")
async def health(db: AsyncSession = Depends(get_db)): 
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ok", "db": "ok"}
    except Exception as e:
        return {"status": "ok", "db": "error", "detail": str(e)}

app.include_router(items_router)
app.include_router(auth_router)

@app.get("/user", response_model=UserRead)
async def get_user(token:str , db: AsyncSession = Depends(get_db)):
    return await  get_current_user(token, session=db)

