from datetime import datetime
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.classification import ClassificationResult
from app.api.agent.prompts import get_classification_prompt
from app.infra.llm import LLMProvider
from app.infra.models import Item, Message   

async def handle_message(
    text: str,
    user_id: uuid.UUID,
    provider: LLMProvider,
    session: AsyncSession,
    current_time: datetime,
) -> list[Item]:
    """
    Saves the raw user message, classifies it using LLM,
    creates corresponding database items, and commits everything in one transaction.
    """
    
    # 1. Save raw message to DB
    user_msg = Message(
        user_id=user_id,
        role="user",
        content=text,
    )
    session.add(user_msg)


    # 2. LLM Classification call
    prompt = get_classification_prompt(text, current_time)
    result: ClassificationResult = await provider.complete(prompt, ClassificationResult)

    # 3. Classified items convert into DB Items
    db_items = []
    for classified in result.items:
        db_item = Item(
            user_id=user_id,
            item_type=classified.type, 
            title=classified.title,
            body=classified.body,
            due_at=classified.due_at,   
            nag_policy=classified.nag_policy,
            source="chat",
            status="open",
            meta={"confidence": classified.confidence} 
        )
        db_items.append(db_item)

    # 4. Save all items to DB
    if db_items:
        session.add_all(db_items)

    # 5. One commit to rule them all!
    await session.commit()

    return db_items