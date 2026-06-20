from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.xninetzy.interfaces.api.deps.auth import require_api_key
from app.xninetzy.core.config import get_settings
from app.xninetzy.os.reminders.reminder_service import ReminderService
from app.xninetzy.os.reminders.reminder_store import ReminderStore
from app.xninetzy.os.reminders.scheduler import run_scheduler_tick

router = APIRouter(prefix="/reminders", tags=["reminders"], dependencies=[Depends(require_api_key)])


class ReminderCreateRequest(BaseModel):
    chat_id: str
    sender_id: str | None = None
    message: str | None = None
    title: str | None = None
    description: str | None = None
    deadline_at: str | None = None
    remind_at: str | None = None
    priority: str = "normal"
    reminder_type: str = "explicit"
    offset_value: int | None = None
    offset_unit: str | None = None
    source: str = "api"
    source_ref_id: str | None = None
    metadata: dict = {}


@router.get("")
async def list_reminders(chat_id: str | None = None, status: str | None = "pending") -> dict:
    return {"reminders": ReminderService().list_reminders(chat_id, status)}


@router.post("")
async def create_reminder(request: ReminderCreateRequest) -> dict:
    svc = ReminderService()
    if request.message:
        return svc.create_from_message(
            request.chat_id,
            request.sender_id,
            request.message,
            source=request.source,
            source_ref_id=request.source_ref_id,
        )
    if not request.title or not request.remind_at:
        return {"created": False, "reason": "title_and_remind_at_required"}
    return svc.create_from_parsed(
        chat_id=request.chat_id,
        user_id=request.sender_id,
        sender_id=request.sender_id,
        source=request.source,
        source_ref_id=request.source_ref_id,
        parsed={
            "title": request.title,
            "description": request.description,
            "deadline_at": request.deadline_at,
            "remind_at": request.remind_at,
            "timezone": get_settings().REMINDER_DEFAULT_TIMEZONE,
            "priority": request.priority,
            "reminder_type": request.reminder_type,
            "offset_value": request.offset_value,
            "offset_unit": request.offset_unit,
            "metadata": request.metadata,
        },
    )


@router.get("/due")
async def due_reminders(limit: int = 50) -> dict:
    tz = ZoneInfo(get_settings().REMINDER_DEFAULT_TIMEZONE or get_settings().APP_TIMEZONE)
    now = datetime.now(tz).isoformat()
    return {"reminders": ReminderStore().get_due_reminders(now, limit=limit)}


@router.post("/{reminder_id}/cancel")
async def cancel_reminder(reminder_id: int) -> dict:
    ReminderService().cancel(reminder_id)
    return {"cancelled": True, "id": reminder_id}


@router.post("/{reminder_id}/close")
async def close_reminder(reminder_id: int) -> dict:
    ReminderService().close(reminder_id)
    return {"closed": True, "id": reminder_id}


@router.delete("/{reminder_id}")
async def delete_cancel_reminder(reminder_id: int) -> dict:
    ReminderService().cancel(reminder_id)
    return {"cancelled": True, "id": reminder_id}


@router.post("/scheduler/tick")
async def scheduler_tick() -> dict:
    return await run_scheduler_tick()
