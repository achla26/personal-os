from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class ClassifiedItem(BaseModel):
    type: Literal["task","grocery","link","read","expense","note"]
    title: str
    body: str | None =None
    due_at: datetime | None = None
    nag_policy: Literal["off","gentle","normal","relentless"]
    confidence: float


class ClassificationResult(BaseModel):
    items: list[ClassifiedItem]    