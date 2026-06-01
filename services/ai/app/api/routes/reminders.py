from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps.auth import require_api_key
from app.reminders.reminder_service import ReminderService

router = APIRouter(prefix="/reminders", tags=["reminders"], dependencies=[Depends(require_api_key)])


class ReminderCreateRequest(BaseModel):
    chat_id: str
    sender_id: str | None = None
    message: str


@router.get("")
async def list_reminders(chat_id: str | None = None) -> dict:
    return {"reminders": ReminderService().list_pending(chat_id)}


@router.post("")
async def create_reminder(request: ReminderCreateRequest) -> dict:
    return ReminderService().create_from_message(request.chat_id, request.sender_id, request.message)


@router.delete("/{reminder_id}")
async def cancel_reminder(reminder_id: int) -> dict:
    ReminderService().cancel(reminder_id)
    return {"cancelled": True, "id": reminder_id}
