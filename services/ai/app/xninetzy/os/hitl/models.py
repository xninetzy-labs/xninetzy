from __future__ import annotations

from pydantic import BaseModel


class ApprovalRequest(BaseModel):
    id: int | None = None
    chat_id: str | None = None
    sender_id: str | None = None
    action_type: str
    title: str
    summary: str | None = None
    payload_json: str = "{}"
    status: str = "pending"
