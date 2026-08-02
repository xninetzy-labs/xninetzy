from __future__ import annotations

import asyncio
from contextlib import contextmanager
from contextvars import ContextVar, Token
from typing import Iterator

EventQueue = asyncio.Queue[dict[str, str]]

_event_queue: ContextVar[EventQueue | None] = ContextVar(
    "xninetzy_chat_event_queue",
    default=None,
)


@contextmanager
def bind_chat_event_queue(queue: EventQueue) -> Iterator[None]:
    token: Token[EventQueue | None] = _event_queue.set(queue)
    try:
        yield
    finally:
        _event_queue.reset(token)


def emit_chat_event(
    event_type: str,
    label: str,
    status: str = "active",
    detail: str | None = None,
) -> None:
    queue = _event_queue.get()
    if queue is None:
        return
    payload = {
        "type": event_type,
        "label": str(label)[:160],
        "status": status if status in {"active", "completed", "failed"} else "active",
    }
    if detail:
        payload["detail"] = str(detail)[:240]
    queue.put_nowait(payload)
