from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.db import get_db
 
from app.infra.models import User
from app.api.routes.items import router as items_router
from app.api.routes.auth import router as auth_router

app = FastAPI()


@app.get("/health")
async def health(db: AsyncSession = Depends(get_db)): 
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ok", "db": "ok"}
    except Exception as e:
        return {"status": "ok", "db": "error", "detail": str(e)}

app.include_router(items_router)
app.include_router(auth_router)

# @app.get("/user")
# async def get_user(db: AsyncSession = Depends(get_db)):
#     return await  get_current_user(session=db)

