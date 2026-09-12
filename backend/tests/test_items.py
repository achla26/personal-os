import pytest
from app.domain.agent.loop import run_agent, MAX_ITERATIONS
from app.domain.agent.tools import ToolContext
from app.infra.llm import FakeAgentProvider
from app.infra.models import Item


@pytest.mark.asyncio
async def test_complete_dentist_flow(db_session, test_user):
    # 1. Direct item creation using db_session and test_user
    dentist = Item(
        user_id=str(test_user.id),
        title="Call dentist",
        item_type="task",
        status="open",
        body="",
        nag_policy="normal",
    )
    db_session.add(dentist)
    await db_session.commit()
    await db_session.refresh(dentist)

    # 2. Scripted LLM tool responses
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

    llm = FakeAgentProvider(script=script)
    ctx = ToolContext(user_id=str(test_user.id), db=db_session)
    
    # 3. Run Agent Loop
    out = await run_agent(
        user_text="dentist wala kaam ho gaya",
        ctx=ctx,
        llm=llm,
    )

    # 4. Assertions
    assert out["stopped_reason"] == "final"
    assert any(t["tool"] == "complete_item" for t in out["trace"])

    await db_session.refresh(dentist)
    assert dentist.status == "done"
    assert dentist.completed_at is not None


@pytest.mark.asyncio
async def test_max_iterations_stops(db_session, test_user):
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

    llm = FakeAgentProvider(script=infinite)
    ctx = ToolContext(user_id=str(test_user.id), db=db_session)
    out = await run_agent(user_text="loop", ctx=ctx, llm=llm)

    assert out["stopped_reason"] == "max_iterations"


@pytest.mark.asyncio
async def test_tool_error_is_data_not_crash(db_session, test_user):
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

    llm = FakeAgentProvider(script=script)
    ctx = ToolContext(user_id=str(test_user.id), db=db_session)
    out = await run_agent(user_text="complete missing", ctx=ctx, llm=llm)

    assert out["stopped_reason"] == "final"
    assert "error" in out["trace"][0]["result"]