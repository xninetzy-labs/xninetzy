from __future__ import annotations

import asyncio
import json
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.config import get_settings
from app.core.logging import logging
from app.reminders.reminder_store import ReminderStore

logger = logging.getLogger(__name__)


async def reminder_loop() -> None:
    settings = get_settings()
    if not settings.REMINDER_ENABLED:
        return
    store = ReminderStore()
    while True:
        now = datetime.now(ZoneInfo(settings.APP_TIMEZONE)).isoformat()
        for reminder in store.due(now):
            try:
                await send_reminder(reminder)
                store.mark_done(int(reminder["id"]))
            except Exception as error:
                logger.warning("Failed to send reminder %s: %s", reminder["id"], error)
        await asyncio.sleep(settings.REMINDER_POLL_INTERVAL_SECONDS)


async def send_reminder(reminder: dict) -> None:
    text = f"⏰ *Reminder*\n\n{reminder['title']}\n"
    if reminder.get("description"):
        text += f"\n{reminder['description']}\n"
    text += f"\n_Dijadwalkan: {reminder['remind_at']}_"
    payload = {"tool": "send_text_message", "input": {"jid": reminder["chat_id"], "text": text}}
    await asyncio.to_thread(_post_mcp_call, payload)


def _post_mcp_call(payload: dict) -> None:
    settings = get_settings()
    request = urllib.request.Request(
        f"{settings.WA_MCP_BASE_URL.rstrip('/')}/mcp/call",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **_auth_header()},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        if response.status >= 400:
            raise RuntimeError(f"WA MCP returned HTTP {response.status}")


def _auth_header() -> dict[str, str]:
    key = get_settings().WA_MCP_API_KEY
    return {"Authorization": f"Bearer {key}"} if key else {}
