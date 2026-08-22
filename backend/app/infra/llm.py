import json
import os
from typing import Protocol
import asyncio 
from groq import AsyncGroq
from pydantic import BaseModel

from app.domain.classification import ClassificationResult
from app.infra.config import settings


class ClassificationError(Exception):
    """Raised when LLM classification completely fails after retries."""
    pass

# ──────────────────────────────────────────────
# 1. INTERFACE 
# ──────────────────────────────────────────────

class LLMProvider(Protocol):
    async def complete(self, prompt: str, schema: type[BaseModel]) -> BaseModel:
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

    async def complete(self, prompt: str, schema: type[BaseModel]) -> BaseModel:
        attempts = 2  # 1st try + 1 retry
        last_error = None

        for attempt in range(attempts):
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are a strict JSON generator. "
                                "You MUST output valid JSON only. "
                                "Do not output thinking tags, explanations, or markdown. "
                                "Your response must strictly start with '{' and end with '}'."
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                    response_format={"type": "json_object"},
                    temperature=self.temperature,
                )

                raw_json = response.choices[0].message.content
                if not raw_json:
                    raise ValueError("LLM returned empty response")

                return schema.model_validate_json(raw_json)

            except Exception as e:
                last_error = e
                if attempt < attempts - 1:
                    # Chhota sa delay retry se pehle
                    await asyncio.sleep(0.5)
                continue

        raise ClassificationError(f"Failed to parse LLM response after {attempts} attempts. Error: {last_error}")


# ──────────────────────────────────────────────
# 3. FAKE PROVIDER — for tests  (no API call)
# ──────────────────────────────────────────────

class FakeProvider:
    """Returns a hardcoded response. No network, no cost, instant."""

    def __init__(self, fixed_response: BaseModel | None = None):
        self.fixed_response = fixed_response

    async def complete(self, prompt: str, schema: type[BaseModel]) -> BaseModel:
        if self.fixed_response:
            return self.fixed_response

        # Default fake response — test mein override kar sakti ho
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