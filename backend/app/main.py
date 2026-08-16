from fastapi import FastAPI, Depends
from sqlalchemy import text
from app.infra.config import settings
from app.infra.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession 


app = FastAPI()

@app.get("/health")
async def health(db: AsyncSession = Depends(get_db)): 
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ok", "db": "ok"}
    except Exception as e:
        return {"status": "ok", "db": "error", "detail": str(e)}


