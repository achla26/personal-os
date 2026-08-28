from fastapi import FastAPI, Depends, HTTPException, Request, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.db import get_db
 
from app.api.routes.items import router as items_router
from app.api.routes.auth import router as auth_router
from app.api.routes.chat import router as chat_router

from app.api.deps import get_current_user
from app.api.schemas import UserRead
from app.infra.core.error_handlers import register_exception_handlers
from app.infra.core.context import set_request_id

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

register_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000","http://192.168.68.51:3000"],
    allow_credentials=True,       #  for cookies
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    #  as req approach create req-id and add in to context
    req_id = set_request_id(request.headers.get("X-Request-ID"))
    #  let the req access other layers
    response = await call_next(request)
    # when response get add client side header ID
    response.headers["X-Request-ID"] = req_id
    return response

@app.get("/health")
async def health(db: AsyncSession = Depends(get_db)): 
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ok", "db": "ok"}
    except Exception as e:
        return {"status": "ok", "db": "error", "detail": str(e)}

app.include_router(items_router)
app.include_router(auth_router)
app.include_router(chat_router)

@app.get("/user", response_model=UserRead)
async def get_user(token:str , db: AsyncSession = Depends(get_db)):
    return await  get_current_user(token, session=db)

