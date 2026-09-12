from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Awaitable, get_type_hints
import inspect

from pydantic import BaseModel, Field, create_model
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
 
from app.infra.models import Item  


@dataclass
class ToolContext:
    """Injected by the agent loop — never exposed to the model."""
    user_id: str
    db: AsyncSession


@dataclass
class Tool:
    name: str
    description: str
    parameters_schema: dict[str, Any]
    handler: Callable[..., Awaitable[Any]]


def tool(fn: Callable[..., Awaitable[Any]]) -> Tool:
    """Register an async function as an agent tool."""
    name = fn.__name__
    description = (fn.__doc__ or "").strip()
    if not description:
        raise ValueError(f"Tool {name} needs a docstring for the model")

    hints = get_type_hints(fn)
    sig = inspect.signature(fn)
    params = list(sig.parameters.keys())

    if not params or params[0] != "ctx":
        raise ValueError(f"Tool {name}: first parameter must be 'ctx: ToolContext'")

    fields: dict[str, Any] = {}
    for key in params[1:]:
        if key not in hints:
            raise ValueError(f"Tool {name}: missing type hint for '{key}'")
        ann = hints[key]
        param = sig.parameters[key]
        if param.default is inspect.Parameter.empty:
            fields[key] = (ann, Field(...))
        else:
            fields[key] = (ann, Field(default=param.default))

    ArgsModel = create_model(f"{name}_args", **fields)
    schema = ArgsModel.model_json_schema()
    parameters_schema = {
        "type": "object",
        "properties": schema.get("properties", {}),
        "required": schema.get("required", []),
        "additionalProperties": False,
    }

    async def handler(ctx: ToolContext, raw_args: dict[str, Any]) -> Any:
        try:
            args = ArgsModel.model_validate(raw_args or {})
            return await fn(ctx, **args.model_dump())
        except Exception as e:
            # Tool errors are data for the model, not process crashes
            return {"error": str(e)}

    return Tool(
        name=name,
        description=description,
        parameters_schema=parameters_schema,
        handler=handler,
    )


def tools_to_provider_schema(tools: list[Tool]) -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters_schema,
            },
        }
        for t in tools
    ]


def _item_to_dict(item: Item) -> dict[str, Any]:
    return {
        "id": str(item.id),
        "title": item.title,
        "item_type": item.item_type,  
        "status": item.status,
        "due_at": item.due_at.isoformat() if item.due_at else None,
        "nag_policy": item.nag_policy,
        "body": item.body,
    }


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@tool
async def search_items(
    ctx: ToolContext,
    query: str = "",
    status: str | None = None,
    item_type: str | None = None,
) -> dict:
    """
    Search the current user's items by free text.

    Use when the user refers to something without an id —
    e.g. "dentist wala kaam", "milk", "what is pending".

    For list-all style questions ("what's on my list", "kya pending hai"):
    use query="" or "*" and status="open".

    status: open | done
    item_type: task | grocery | link | read | expense | note

    Returns id, title, item_type, status, due_at. Never invent rows.
    """
    stmt = select(Item).where(Item.user_id == ctx.user_id)

    generic = {
        "", "*", "all", "sab", "list", "items", "item", "everything",
        "pending", "open", "todo", "tasks",
    }
    q = (query or "").strip().lower()

    if q and q not in generic:
        stmt = stmt.where(Item.title.ilike(f"%{q}%"))

    if status:
        # map common aliases
        status_norm = "open" if status in ("pending", "open", "todo") else status
        if status_norm in ("done", "completed"):
            status_norm = "done"
        stmt = stmt.where(Item.status == status_norm)
    elif q in generic or not q:
        stmt = stmt.where(Item.status == "open")

    if item_type:
        stmt = stmt.where(Item.item_type == item_type.lower())

    stmt = stmt.order_by(Item.created_at.desc()).limit(20)
    result = await ctx.db.execute(stmt)
    rows = result.scalars().all()
    return {"items": [_item_to_dict(i) for i in rows], "count": len(rows)}


@tool
async def complete_item(
    ctx: ToolContext,
    item_id: str,
) -> dict:
    """
    Mark one item as done by its id string (from search_items).

    Use after search_items when the user says work is finished —
    e.g. "dentist wala kaam ho gaya".

    Pass the real id from search_items. Do not guess ids.
    """
    stmt = select(Item).where(
        Item.id == item_id,
        Item.user_id == ctx.user_id,
    )
    result = await ctx.db.execute(stmt)
    item = result.scalar_one_or_none()

    if item is None:
        return {"error": f"No item found with id={item_id} for this user"}

    if item.status == "done":
        return {"ok": True, "message": "Already done", "item": _item_to_dict(item)}

    item.status = "done"
    item.completed_at = datetime.now(timezone.utc)
    item.next_nag_at = None

    await ctx.db.commit()
    await ctx.db.refresh(item)
    return {"ok": True, "item": _item_to_dict(item)}


@tool
async def create_item(
    ctx: ToolContext,
    title: str,
    item_type: str = "task",
    due_at: str | None = None,
    nag_policy: str | None = None,
    body: str | None = None,
) -> dict:
    """
    Create a new item for the user.

    item_type: task | grocery | link | read | expense | note
    due_at: ISO datetime or date if mentioned, else null
    nag_policy: gentle | normal | relentless | off
    """
    allowed = {"task", "grocery", "link", "read", "expense", "note"}
    t = (item_type or "task").lower()
    if t not in allowed:
        return {"error": f"Invalid type '{item_type}'. Use one of {sorted(allowed)}"}

    parsed_due = None
    if due_at:
        try:
            parsed_due = datetime.fromisoformat(due_at.replace("Z", "+00:00"))
        except ValueError:
            return {"error": f"Invalid due_at '{due_at}'. Use ISO format."}

    item = Item(
        user_id=ctx.user_id,
        title=title.strip(),
        item_type=t,
        status="open",
        due_at=parsed_due,
        body=body or "",
        nag_policy=nag_policy or "normal",
    )
    # If your Item generates ULID in default/on_init, fine; else set id here

    ctx.db.add(item)
    await ctx.db.commit()
    await ctx.db.refresh(item)
    return {"ok": True, "item": _item_to_dict(item)}


@tool
async def create_item(
    ctx: ToolContext,
    title: str,
    item_type: str = "task",
    due_date: str | None = None,
    nag_policy: str | None = None,
) -> dict:
    """
    Create a new item for the user.

    Use when the user clearly wants something new saved and search shows
    it does not already exist. Prefer search_items first if they might
    be talking about an existing item.

    item_type: task | grocery | link | read | expense | note
    due_date: ISO date string YYYY-MM-DD if mentioned, else null
    nag_policy: gentle | normal | relentless | off — optional
    """
    allowed = {"task", "grocery", "link", "read", "expense", "note"}
    t = (item_type or "task").lower()
    if t not in allowed:
        return {"error": f"Invalid type '{item_type}'. Use one of {sorted(allowed)}"}

    parsed_due = None
    if due_date:
        try:
            parsed_due = datetime.fromisoformat(due_date).date()
        except ValueError:
            return {"error": f"Invalid due_date '{due_date}'. Use YYYY-MM-DD"}

    item = Item(
        user_id=ctx.user_id,
        title=title.strip(),
        type=t,
        status="pending",
        due_date=parsed_due,
    )
    if nag_policy is not None and hasattr(item, "nag_policy"):
        item.nag_policy = nag_policy

    ctx.db.add(item)
    await ctx.db.commit()
    await ctx.db.refresh(item)
    return {"ok": True, "item": _item_to_dict(item)}


ALL_TOOLS: list[Tool] = [search_items, complete_item, create_item]
TOOL_MAP: dict[str, Tool] = {t.name: t for t in ALL_TOOLS}