from __future__ import annotations

import json
import time
from typing import Any

from app.domain.agent.tools import (
    ALL_TOOLS,
    TOOL_MAP,
    ToolContext,
    tools_to_provider_schema,
)

MAX_ITERATIONS = 10
MAX_WALL_SECONDS = 30.0


SYSTEM_PROMPT = """You are Personal OS, a careful personal assistant.

You help the user capture and manage items (tasks, groceries, expenses, notes, links, reading).

Rules:
- When the user refers to something without an id, call search_items first.
- When they say something is finished, search then complete_item with the real id.
- When they want something new saved, create_item (search first if it might already exist).
- Never invent item ids. Never claim success without a tool result.
- Prefer few tool calls. After tools finish, give a short clear reply in the user's language.
- If a tool returns error or empty items, adjust filters or tell the user honestly.

- Open items use status "open" (not "pending").
- Item ids are strings like "01a046af-...". Always copy id exactly from search_items. 
"""


class AgentLimitError(Exception):
    pass


async def run_agent(
    *,
    user_text: str,
    ctx: ToolContext,
    llm: Any,
    max_iterations: int = MAX_ITERATIONS,
    max_wall_seconds: float = MAX_WALL_SECONDS,
) -> dict[str, Any]:
    """
    Core tool loop (Claude Code-style):

        while True:
            r = model(messages, tools)
            if no tool calls: return text
            execute tools, append results, continue

    Limits stop runaway cost/loops.
    """
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_text},
    ]
    tools_schema = tools_to_provider_schema(ALL_TOOLS)
    started = time.monotonic()
    trace: list[dict[str, Any]] = []

    for iteration in range(max_iterations):
        if time.monotonic() - started > max_wall_seconds:
            return {
                "text": "Ye kaam poora nahi kar paya (time limit). Thoda simple karke bolo.",
                "trace": trace,
                "stopped_reason": "max_time",
            }

        # llm.chat_with_tools must return a normalized dict — see below
        response = await llm.chat_with_tools(messages=messages, tools=tools_schema)
        tool_calls = response.get("tool_calls") or []
        text = (response.get("text") or "").strip()

        if not tool_calls:
            return {
                "text": text or "Ho gaya.",
                "trace": trace,
                "stopped_reason": "final",
            }

        # Assistant turn that requested tools (OpenAI-compatible shape)
        messages.append(
            {
                "role": "assistant",
                "content": response.get("text") or None,
                "tool_calls": tool_calls,
            }
        )

        for call in tool_calls:
            if time.monotonic() - started > max_wall_seconds:
                break

            call_id = call["id"]
            fn_name = call["function"]["name"]
            raw_args = call["function"].get("arguments") or {}
            if isinstance(raw_args, str):
                try:
                    raw_args = json.loads(raw_args) if raw_args else {}
                except json.JSONDecodeError:
                    raw_args = {}

            tool = TOOL_MAP.get(fn_name)
            if tool is None:
                result: Any = {"error": f"Unknown tool: {fn_name}"}
            else:
                result = await tool.handler(ctx, raw_args)

            trace.append({"tool": fn_name, "args": raw_args, "result": result})

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call_id,
                    "name": fn_name,
                    "content": json.dumps(result, default=str),
                }
            )

    return {
        "text": "Ye kaam poora nahi kar paya, thoda simple karke bolo.",
        "trace": trace,
        "stopped_reason": "max_iterations",
    }