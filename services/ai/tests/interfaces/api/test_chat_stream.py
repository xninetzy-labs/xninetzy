from __future__ import annotations

import asyncio

import pytest

from app.xninetzy.interfaces.api.routes import chat as chat_route
from app.xninetzy.schemas.chat import ChatRequest, ChatResponse


@pytest.mark.asyncio
async def test_chat_stream_emits_lifecycle_delta_and_done(monkeypatch):
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

    assert "event: run_started" in payload
    assert "event: phase" in payload
    assert "event: delta" in payload
    assert "grounded reply" in payload
    assert "event: done" in payload


@pytest.mark.asyncio
async def test_chat_stream_emits_heartbeat_during_silent_work(monkeypatch):
    async def fake_chat(request: ChatRequest) -> ChatResponse:
        await asyncio.sleep(0.03)
        return ChatResponse(reply="done")

    monkeypatch.setattr(chat_route, "chat", fake_chat)
    monkeypatch.setattr(chat_route, "CHAT_STREAM_HEARTBEAT_SECONDS", 0.01)
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

    assert "event: heartbeat" in payload


def test_direct_tool_catalog_formatter_hides_python_enum_repr():
    result = chat_route._format_direct_tool_result(
        "tool_catalog",
        [
            {
                "name": "web_search",
                "feature_pack": "research",
                "risk": "read",
                "description": "Search trusted web sources.",
            }
        ],
    )

    assert "web_search · research · read" in result
    assert "<FeaturePack" not in result
