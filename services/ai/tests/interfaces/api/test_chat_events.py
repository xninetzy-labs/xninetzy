from __future__ import annotations

import asyncio

import pytest

from app.xninetzy.interfaces.api.chat_events import (
    bind_chat_event_queue,
    emit_chat_event,
)


@pytest.mark.asyncio
async def test_chat_events_are_scoped_and_sanitized() -> None:
    queue: asyncio.Queue[dict[str, str]] = asyncio.Queue()

    emit_chat_event("phase", "outside")

    with bind_chat_event_queue(queue):
        emit_chat_event("activity", "a" * 200, "unexpected", "b" * 300)

    event = queue.get_nowait()

    assert event["type"] == "activity"
    assert event["status"] == "active"
    assert len(event["label"]) == 160
    assert len(event["detail"]) == 240
    assert queue.empty()
