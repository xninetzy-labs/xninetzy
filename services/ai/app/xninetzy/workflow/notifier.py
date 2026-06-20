"""Short WhatsApp progress updates between workflow steps.

Keeps the user informed ("✅ Step 2/6 selesai: …") without spamming: respects
config toggles, a min-interval rate limit, a max message length, and only fires
for "big" actions. Never sends raw tracebacks; detail stays in server logs.
"""

from __future__ import annotations

import time

from app.xninetzy.core.config import get_settings
from app.xninetzy.core.logging import logging
from app.xninetzy.workflow.models import WorkflowAction, WorkflowPlan

logger = logging.getLogger(__name__)

# Trivial steps that should never produce a WA ping.
_QUIET_TYPES: set[str] = set()


class WorkflowNotifier:
    def __init__(self, chat_id: str, *, enabled: bool | None = None, send=None):
        s = get_settings()
        self.chat_id = chat_id
        self.settings = s
        self.enabled = s.WORKFLOW_NOTIFY_ENABLED if enabled is None else enabled
        self._send = send  # injectable for tests; defaults to wa_tools sender
        self._last_sent_at = 0.0

    async def _dispatch(self, text: str) -> None:
        if not self.enabled or not text:
            return
        max_len = self.settings.WORKFLOW_NOTIFY_MAX_MESSAGE_LENGTH
        if len(text) > max_len:
            text = text[: max_len - 1].rstrip() + "…"
        # Rate limit (skip the wait for the very first message).
        interval = self.settings.WORKFLOW_NOTIFY_MIN_INTERVAL_SECONDS
        now = time.monotonic()
        if self._last_sent_at and (now - self._last_sent_at) < interval:
            elapsed = now - self._last_sent_at
            await _sleep(interval - elapsed)
        try:
            await self._sender()(self.chat_id, text)
            self._last_sent_at = time.monotonic()
            logger.info("workflow_notify_sent chat_id=%s len=%d", self.chat_id, len(text))
        except Exception as exc:  # pragma: no cover - WA transport failure
            logger.warning("workflow_notify_failed chat_id=%s err=%s", self.chat_id, exc)

    def _sender(self):
        if self._send is not None:
            return self._send
        from app.xninetzy.interfaces.whatsapp.client import call_wa_tool

        async def _send_text(chat_id: str, text: str) -> None:
            await call_wa_tool("send_text_message", {"jid": chat_id, "text": text})

        return _send_text

    def _step_label(self, plan: WorkflowPlan, action: WorkflowAction) -> str:
        total = max(1, len([a for a in plan.actions]))
        idx = next((i + 1 for i, a in enumerate(plan.actions) if a.id == action.id), 0)
        return f"{idx}/{total}"

    async def notify_action_started(self, plan: WorkflowPlan, action: WorkflowAction) -> None:
        if not self.settings.WORKFLOW_NOTIFY_ON_START or not action.notify_on_done:
            return
        await self._dispatch(f"⏳ Step {self._step_label(plan, action)}: {action.title}…")

    async def notify_action_done(self, plan: WorkflowPlan, action: WorkflowAction) -> None:
        if not self.settings.WORKFLOW_NOTIFY_ON_DONE or not action.notify_on_done:
            return
        summary = (action.result_summary or "selesai").strip()
        await self._dispatch(f"✅ Step {self._step_label(plan, action)} selesai\n{summary}")

    async def notify_action_failed(self, plan: WorkflowPlan, action: WorkflowAction) -> None:
        if not action.notify_on_done:
            return
        reason = (action.error or "tidak diketahui").strip()
        await self._dispatch(f"⚠️ Step {self._step_label(plan, action)} gagal: {reason}")

    async def notify_final(self, plan: WorkflowPlan, summary_line: str) -> None:
        await self._dispatch(f"🎯 Workflow selesai\n{summary_line}".strip())


async def _sleep(seconds: float) -> None:
    import asyncio

    if seconds > 0:
        await asyncio.sleep(seconds)
