from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ItemCreate(BaseModel):
    title: str
    item_type: str
    body: str | None = None
    due_at: datetime | None = None
    nag_policy: str | None = None


class ItemUpdate(BaseModel):
    title: str | None = None
    item_type: str | None = None
    body: str | None = None
    due_at: datetime | None = None
    nag_policy: str | None = None
    status:  str | None = None


class ItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    title: str
    item_type: str
    body: str | None = None
    due_at: datetime | None = None 
    status: str | None = None    
    nag_policy : str |None = None 
    nag_count: int
    meta: dict[str, Any] = Field(default_factory=dict)    
    next_nag_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class UserCreate(BaseModel):
    name: str
    email: str
    password: str


class UserUpdate(BaseModel):
    name: str
    email: str
    password: str


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    email: str
    created_at: datetime
    updated_at: datetime


class AuthResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserRead


class SigninInput(BaseModel):
    email: str = "ashlin@gmail.com"    
    password: str = "password123"

class SignupInput(UserCreate):
    pass


class ChatRequest(BaseModel):
    text: str

class ChatResponse(BaseModel):
    items: list[ItemRead]

class GroupedItems(BaseModel):
    overdue: list[ItemRead]
    today: list[ItemRead]
    this_week: list[ItemRead]
    someday: list[ItemRead]