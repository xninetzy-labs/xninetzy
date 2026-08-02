from __future__ import annotations

import pytest

from app.xninetzy.interfaces.api.routes import chat as chat_route
from app.xninetzy.schemas.chat import ChatRequest, ChatResponse


@pytest.mark.asyncio
async def test_chat_stream_emits_safe_status_response_and_done(monkeypatch):
    async def fake_chat(request: ChatRequest) -> ChatResponse:
        return ChatResponse(reply="grounded reply")

    monkeypatch.setattr(chat_route, "chat", fake_chat)
    response = await chat_route.chat_stream(
        ChatRequest(
            chat_id="owner",
            sender_id="owner",
            sender_name="Owner",
            message="hello",
            chat_type="private",
        )
    )
    payload = "".join([chunk async for chunk in response.body_iterator])

    assert "event: status" in payload
    assert "Preparing grounded response" in payload
    assert "event: response" in payload
    assert "grounded reply" in payload
    assert "event: done" in payload
