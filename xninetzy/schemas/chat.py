from typing import Any, Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    chat_id: str = Field(..., min_length=1)
    sender_id: str | None = None
    sender_name: str | None = None
    message: str = Field(..., min_length=1)
    chat_type: Literal["private", "group"] = "private"
    group_name: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    reply: str
