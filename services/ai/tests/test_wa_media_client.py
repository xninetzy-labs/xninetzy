"""Offline tests for WA media client wrappers (MCP call mocked)."""

from __future__ import annotations

import pytest

from app.wa_tools import client as wa_client
from app.wa_tools.client import WaToolError


@pytest.mark.asyncio
async def test_download_media_message_success(monkeypatch):
    async def fake_call(tool, input_data):
        assert tool == "download_media_message"
        assert input_data["chat_id"] == "628@s.whatsapp.net"
        assert input_data["message_id"] == "MSG1"
        return {"success": True, "tool": tool, "result": {
            "local_path": "/app/data/wa-media/628/MSG1/file.pdf",
            "filename": "file.pdf", "mime_type": "application/pdf",
            "size_bytes": 1234, "sha256": "abc",
        }}

    monkeypatch.setattr(wa_client, "call_wa_tool", fake_call)
    out = await wa_client.download_media_message("628@s.whatsapp.net", "MSG1")
    assert out["ok"] is True
    assert out["filename"] == "file.pdf"
    assert out["local_path"].endswith("file.pdf")


@pytest.mark.asyncio
async def test_download_media_message_cache_miss_friendly(monkeypatch):
    async def fake_call(tool, input_data):
        raise WaToolError("Message MSG2 not found in cache. Media may have expired.")

    monkeypatch.setattr(wa_client, "call_wa_tool", fake_call)
    out = await wa_client.download_media_message("628@s.whatsapp.net", "MSG2")
    assert out["ok"] is False
    assert "kirim ulang" in out["error"].lower()


@pytest.mark.asyncio
async def test_download_media_message_generic_error(monkeypatch):
    async def fake_call(tool, input_data):
        raise WaToolError("socket dead")

    monkeypatch.setattr(wa_client, "call_wa_tool", fake_call)
    out = await wa_client.download_media_message("628@s.whatsapp.net", "MSG3")
    assert out["ok"] is False
    assert "socket dead" in out["error"]


@pytest.mark.asyncio
async def test_download_passes_participant(monkeypatch):
    seen = {}

    async def fake_call(tool, input_data):
        seen.update(input_data)
        return {"success": True, "result": {"local_path": "/x"}}

    monkeypatch.setattr(wa_client, "call_wa_tool", fake_call)
    await wa_client.download_media_message("g@g.us", "M", participant_jid="628@s.whatsapp.net")
    assert seen["participant_jid"] == "628@s.whatsapp.net"


@pytest.mark.asyncio
async def test_get_message_metadata(monkeypatch):
    async def fake_call(tool, input_data):
        return {"success": True, "result": {"has_media": True, "media_type": "image"}}

    monkeypatch.setattr(wa_client, "call_wa_tool", fake_call)
    out = await wa_client.get_message_metadata("628@s.whatsapp.net", "MSG1")
    assert out["ok"] is True and out["has_media"] is True
