import json
import os
from typing import Protocol

from groq import AsyncGroq
from pydantic import BaseModel

from app.domain.classification import ClassificationResult
from app.infra.config import settings

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
    ):
        self.client = AsyncGroq(
            api_key=api_key or settings.LLM_API_KEY,
        )
        self.model = model or settings.LLM_MODEL

    async def complete(self, prompt: str, schema: type[BaseModel]) -> BaseModel:
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
            temperature=0.1,
        )

        raw_json = response.choices[0].message.content

        if not raw_json:
            raise ValueError("LLM returned empty response")

        # Pydantic validates + parses in one step
        return schema.model_validate_json(raw_json)


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