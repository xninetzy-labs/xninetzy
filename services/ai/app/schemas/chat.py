from typing import Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    chat_id: str = Field(..., min_length=1)
    sender_id: str = Field(..., min_length=1)
    sender_name: str | None = None
    message: str = Field(..., min_length=1)
    chat_type: Literal["private", "group"]
    group_name: str | None = None


class ChatResponse(BaseModel):
    reply: str
