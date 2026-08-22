import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_llm_provider
from app.domain.classification import ClassificationResult
from app.infra.llm import FakeProvider
from app.infra.models import Item, Message
from app.main import app 

@pytest.mark.asyncio
async def test_chat_creates_message_and_items(
    auth_client: AsyncClient,
    db_session: AsyncSession,
):
    # 1. Arrange: Fake response setup 
    fake_result = ClassificationResult.model_validate({
        "items": [
            {
                "type": "grocery",
                "title": "Milk",
                "body": None,
                "due_at": None,
                "nag_policy": "gentle",
                "confidence": 0.98,
            },
            {
                "type": "task",
                "title": "Call dentist",
                "body": None,
                "due_at": None,
                "nag_policy": "normal",
                "confidence": 0.95,
            },
        ]
    })
    fake_provider = FakeProvider(fixed_response=fake_result)

    # Dependency Override:  Groq swap into FakeProvider 
    app.dependency_overrides[get_llm_provider] = lambda: fake_provider

    try:
        # 2. Act: POST /chat call 
        payload = {"text": "milk and call dentist "}
        response = await auth_client.post("/chat", json=payload)

        # 3. Assert: API Response verify karo
        assert response.status_code == 201
        data = response.json()
        assert len(data["items"]) == 2
        assert data["items"][0]["title"] == "Milk"
        assert data["items"][1]["title"] == "Call dentist"

        # 4. Assert: In Database Message and Items check 
        # Check Message table
        msg_result = await db_session.execute(
            select(Message).where(Message.content == payload["text"])
        )
        saved_msg = msg_result.scalar_one_or_none()
        assert saved_msg is not None
        assert saved_msg.role == "user"

        # Check Item table
        items_result = await db_session.execute(
            select(Item).where(Item.title.in_(["Milk", "Call dentist"]))
        )
        saved_items = items_result.scalars().all()
        assert len(saved_items) == 2

    finally:
        # Cleanup overrides
        app.dependency_overrides.pop(get_llm_provider, None)