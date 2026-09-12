import asyncio
import json
import time
from typing import Any, Protocol

from groq import AsyncGroq, AuthenticationError, BadRequestError, PermissionDeniedError
from pydantic import BaseModel

from app.domain.classification import ClassificationResult
from app.infra.config import settings
from app.infra.core.context import get_request_id


class ClassificationError(Exception):
    """Raised when LLM classification completely fails after retries."""
    pass


class LLMError(Exception):
    """Raised when a generic LLM chat/tools call fails after retries."""
    pass


def is_retryable_error(e: Exception) -> bool:
    if isinstance(e, AuthenticationError):  # 401
        return False
    if isinstance(e, PermissionDeniedError):
        return False
    
    if isinstance(e, BadRequestError):
        return "json_validate_failed" in str(e)

    return True


def estimate_cost(tokens_in: int, tokens_out: int) -> float:
    cost_in = (tokens_in / 1_000_000) * 0.05
    cost_out = (tokens_out / 1_000_000) * 0.08
    return round(cost_in + cost_out, 6)


# ──────────────────────────────────────────────
# 1. INTERFACE
# ──────────────────────────────────────────────

class LLMProvider(Protocol):
    async def complete(
        self,
        prompt: str,
        schema: type[BaseModel],
        system_prompt: str | None = None,
    ) -> BaseModel:
        """Send a prompt, get back a validated Pydantic model."""
        ...

    async def chat_with_tools(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Agent turn.
        Returns:
          {
            "text": str | None,
            "tool_calls": [
              {
                "id": str,
                "type": "function",
                "function": {"name": str, "arguments": str},  # arguments = JSON string
              }
            ],
          }
        """
        ...


# ──────────────────────────────────────────────
# 2. REAL PROVIDER — Groq
# ──────────────────────────────────────────────

class GroqProvider:
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        temperature: float = 0.1,
    ):
        self.client = AsyncGroq(api_key=api_key or settings.LLM_API_KEY)
        self.model = model or settings.LLM_MODEL
        self.temperature = temperature

    async def complete(
        self,
        prompt: str,
        schema: type[BaseModel],
        system_prompt: str | None = None,
    ) -> BaseModel:
        messages: list[dict[str, Any]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        else:
            messages.append(
                {
                    "role": "system",
                    "content": "You are a JSON-only API backend. Return raw JSON.",
                }
            )
        messages.append({"role": "user", "content": prompt})

        max_attempts = 3
        last_error = None

        for attempt in range(max_attempts):
            start_time = time.perf_counter()
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    response_format={"type": "json_object"},
                    temperature=self.temperature,
                )

                latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
                raw_json = response.choices[0].message.content
                if not raw_json:
                    raise ValueError("LLM returned empty response")

                result = schema.model_validate_json(raw_json)

                usage = response.usage
                tokens_in = usage.prompt_tokens if usage else 0
                tokens_out = usage.completion_tokens if usage else 0
                cost = estimate_cost(tokens_in, tokens_out)
                req_id = get_request_id()

                print(
                    f"🤖 [LLM OK] req_id={req_id} "
                    f"attempt={attempt + 1} "
                    f"latency_ms={latency_ms}ms "
                    f"tokens_in={tokens_in} "
                    f"tokens_out={tokens_out} "
                    f"cost_est=${cost:.6f}"
                )
                return result

            except Exception as e:
                last_error = e
                latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
                print(
                    f"❌ [LLM FAIL] model={self.model} attempt={attempt + 1} "
                    f"latency_ms={latency_ms}ms error={e}"
                )

                if not is_retryable_error(e):
                    raise ClassificationError(f"Non-retryable LLM Error: {e}") from e

                if attempt == max_attempts - 1:
                    break

                await asyncio.sleep(1 * (2**attempt))

        raise ClassificationError(
            f"LLM failed after {max_attempts} attempts. Last error: {last_error}"
        )

    async def chat_with_tools(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        One agent step: model may return text and/or tool_calls.
        Do NOT use response_format=json_object here — tools need normal chat.
        """
        max_attempts = 3
        last_error = None

        for attempt in range(max_attempts):
            start_time = time.perf_counter()
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=tools or None,
                    tool_choice="auto",
                    temperature=0.2,
                )

                latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
                msg = response.choices[0].message

                tool_calls: list[dict[str, Any]] = []
                if msg.tool_calls:
                    for tc in msg.tool_calls:
                        tool_calls.append(
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.function.name,
                                    # Keep as JSON string — loop will json.loads
                                    "arguments": tc.function.arguments or "{}",
                                },
                            }
                        )

                usage = response.usage
                tokens_in = usage.prompt_tokens if usage else 0
                tokens_out = usage.completion_tokens if usage else 0
                cost = estimate_cost(tokens_in, tokens_out)
                req_id = get_request_id()

                print(
                    f"🤖 [LLM TOOLS] req_id={req_id} "
                    f"attempt={attempt + 1} "
                    f"latency_ms={latency_ms}ms "
                    f"tools={len(tool_calls)} "
                    f"tokens_in={tokens_in} "
                    f"tokens_out={tokens_out} "
                    f"cost_est=${cost:.6f}"
                )

                return {
                    "text": msg.content,
                    "tool_calls": tool_calls,
                }

            except Exception as e:
                last_error = e
                latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
                print(
                    f"❌ [LLM TOOLS FAIL] model={self.model} attempt={attempt + 1} "
                    f"latency_ms={latency_ms}ms error={e}"
                )

                if not is_retryable_error(e):
                    raise LLMError(f"Non-retryable LLM Error: {e}") from e

                if attempt == max_attempts - 1:
                    break

                await asyncio.sleep(1 * (2**attempt))

        raise LLMError(
            f"chat_with_tools failed after {max_attempts} attempts. Last error: {last_error}"
        )


# ──────────────────────────────────────────────
# 3. FAKE PROVIDERS — tests
# ──────────────────────────────────────────────

class FakeProvider:
    """M1 classifier fake. Also satisfies Protocol with empty tools response."""

    def __init__(self, fixed_response: BaseModel | None = None):
        self.fixed_response = fixed_response

    async def complete(
        self,
        prompt: str,
        schema: type[BaseModel],
        system_prompt: str | None = None,
    ) -> BaseModel:
        if self.fixed_response:
            return self.fixed_response

        return ClassificationResult.model_validate(
            {
                "items": [
                    {
                        "type": "task",
                        "title": "Fake task from test",
                        "body": None,
                        "due_at": None,
                        "nag_policy": "normal",
                        "confidence": 0.99,
                    }
                ]
            }
        )

    async def chat_with_tools(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> dict[str, Any]:
        # Safe default so old tests don't break if something calls tools
        return {"text": "ok", "tool_calls": []}


class FakeAgentProvider:
    """
    Scripted agent turns for M2 tests.
    Each script item:
      {"text": str|None, "tool_calls": [...]}
    """

    def __init__(self, script: list[dict[str, Any]] | None = None):
        self.script = list(script or [])
        self.calls = 0
        self.last_messages: list[dict[str, Any]] | None = None

    async def complete(
        self,
        prompt: str,
        schema: type[BaseModel],
        system_prompt: str | None = None,
    ) -> BaseModel:
        raise NotImplementedError("FakeAgentProvider is for chat_with_tools only")

    async def chat_with_tools(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> dict[str, Any]:
        self.last_messages = messages
        self.calls += 1
        if not self.script:
            return {"text": "done", "tool_calls": []}
        return self.script.pop(0)