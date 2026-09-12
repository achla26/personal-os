import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.agent.loop import run_agent, MAX_ITERATIONS
from app.domain.agent.tools import ToolContext
from app.infra.llm import FakeAgentProvider
from app.infra.models import Item, User
from app.infra.security import hash_password


async def _make_user(db_session: AsyncSession) -> User:
    user = User(
        name="Agent Test",
        email=f"agent-{id(db_session)}@example.com",
        password_hash=hash_password("password123"),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def _make_dentist_item(db_session: AsyncSession, user_id: str) -> Item:
    item = Item(
        user_id=user_id,
        title="Call dentist",
        item_type="task",
        status="open",
        body="",
        nag_policy="normal",
    )
    db_session.add(item)
    await db_session.commit()
    await db_session.refresh(item)
    return item


@pytest.mark.asyncio
async def test_complete_dentist_flow(db_session: AsyncSession):
    user = await _make_user(db_session)
    dentist = await _make_dentist_item(db_session, str(user.id))

    script = [
        {
            "text": None,
            "tool_calls": [
                {
                    "id": "1",
                    "type": "function",
                    "function": {
                        "name": "search_items",
                        "arguments": '{"query": "dentist", "status": "open"}',
                    },
                }
            ],
        },
        {
            "text": None,
            "tool_calls": [
                {
                    "id": "2",
                    "type": "function",
                    "function": {
                        "name": "complete_item",
                        "arguments": f'{{"item_id": "{dentist.id}"}}',
                    },
                }
            ],
        },
        {"text": "Dentist wala kaam done mark kar diya.", "tool_calls": []},
    ]

    llm = FakeAgentProvider(script)
    ctx = ToolContext(user_id=str(user.id), db=db_session)
    out = await run_agent(
        user_text="dentist wala kaam ho gaya",
        ctx=ctx,
        llm=llm,
    )

    assert out["stopped_reason"] == "final"
    assert any(t["tool"] == "complete_item" for t in out["trace"])

    await db_session.refresh(dentist)
    assert dentist.status == "done"
    assert dentist.completed_at is not None


@pytest.mark.asyncio
async def test_max_iterations_stops(db_session: AsyncSession):
    user = await _make_user(db_session)

    infinite = [
        {
            "text": None,
            "tool_calls": [
                {
                    "id": str(i),
                    "type": "function",
                    "function": {
                        "name": "search_items",
                        "arguments": '{"query": "x"}',
                    },
                }
            ],
        }
        for i in range(MAX_ITERATIONS + 5)
    ]

    llm = FakeAgentProvider(infinite)
    ctx = ToolContext(user_id=str(user.id), db=db_session)
    out = await run_agent(user_text="loop", ctx=ctx, llm=llm)

    assert out["stopped_reason"] == "max_iterations"


@pytest.mark.asyncio
async def test_tool_error_is_data_not_crash(db_session: AsyncSession):
    user = await _make_user(db_session)

    script = [
        {
            "text": None,
            "tool_calls": [
                {
                    "id": "1",
                    "type": "function",
                    "function": {
                        "name": "complete_item",
                        "arguments": '{"item_id": "01impossible0000000000000000"}',
                    },
                }
            ],
        },
        {"text": "Woh item nahi mili.", "tool_calls": []},
    ]

    llm = FakeAgentProvider(script)
    ctx = ToolContext(user_id=str(user.id), db=db_session)
    out = await run_agent(user_text="complete missing", ctx=ctx, llm=llm)

    assert out["stopped_reason"] == "final"
    assert "error" in out["trace"][0]["result"]