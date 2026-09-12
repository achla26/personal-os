from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_llm_provider
from app.infra.core.time import now_nz
from app.domain.inbox import handle_message
from app.infra.llm import ClassificationError, LLMProvider
from app.infra.models import User
from app.api.schemas import ChatResponse,ChatRequest

from app.domain.agent.loop import run_agent
from app.domain.agent.tools import ToolContext

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatIn(BaseModel):
    message: str


@router.post("", response_model=ChatResponse, status_code=status.HTTP_201_CREATED)
async def chat_message(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    provider: LLMProvider = Depends(get_llm_provider),
):
    """
    Takes a raw text message from the user, classifies it into items,
    saves them to DB, and returns the created items.
    """
    if not payload.text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty",
        )

    try:
        # Domain orchestrator call
        items = await handle_message(
            text=payload.text,
            user_id=current_user.id,
            provider=provider,
            session=session,
            current_time=now_nz(),
        )
        return ChatResponse(items=items)

    except ClassificationError as e:
        # LLM fail hone par 502 (Bad Gateway)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI Classification service failed: {str(e)}",
        )



@router.post("/agent")
async def chat_agent(
    payload: ChatIn, 
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
    llm=Depends(get_llm_provider),
):
    ctx = ToolContext(user_id=user.id, db=db)
    result = await run_agent(user_text=payload.message, ctx=ctx, llm=llm)
    return {
        "reply": result["text"],
        "trace": result["trace"],  # optional: hide in prod later
        "stopped_reason": result["stopped_reason"],
    }    