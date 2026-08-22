import asyncio
import os
import time
from typing import Protocol

from groq import AsyncGroq, AuthenticationError, BadRequestError, PermissionDeniedError
from pydantic import BaseModel

from app.domain.classification import ClassificationResult
from app.infra.config import settings
from app.infra.core.context import get_request_id


class ClassificationError(Exception):
    """Raised when LLM classification completely fails after retries."""
    pass


def is_retryable_error(e: Exception) -> bool:
    if isinstance(e, AuthenticationError):  # 401
        return False
    if isinstance(e, PermissionDeniedError):  # 403
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


# ──────────────────────────────────────────────
# 2. REAL PROVIDER — Groq (production)
# ──────────────────────────────────────────────

class GroqProvider:
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        temperature: float = 0.1,
    ):
        self.client = AsyncGroq(
            api_key=api_key or settings.LLM_API_KEY,
        )
        self.model = model or settings.LLM_MODEL
        self.temperature = temperature 

    async def complete(
        self,
        prompt: str,
        schema: type[BaseModel],
        system_prompt: str | None = None,
    ) -> BaseModel:

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        else:
            messages.append({"role": "system", "content": "You are a JSON-only API backend. Return raw JSON."})

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
                print(f"❌ [LLM FAIL] model={self.model} attempt={attempt + 1} latency_ms={latency_ms}ms error={e}")

                if not is_retryable_error(e):
                    raise ClassificationError(f"Non-retryable LLM Error: {e}") from e

                if attempt == max_attempts - 1:
                    break

                sleep_seconds = 1 * (2 ** attempt)
                await asyncio.sleep(sleep_seconds)

        raise ClassificationError(f"LLM failed after {max_attempts} attempts. Last error: {last_error}")


# ──────────────────────────────────────────────
# 3. FAKE PROVIDER — for tests (no API call)
# ──────────────────────────────────────────────

class FakeProvider:
    """Returns a hardcoded response. No network, no cost, instant."""

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

        return ClassificationResult.model_validate({
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
        })