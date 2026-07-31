"""Offline tests for WhatsApp media send tools (wa-enggine calls mocked)."""

from __future__ import annotations

import pytest

from app.xninetzy.interfaces.whatsapp import messaging
from app.xninetzy.interfaces.whatsapp.client import WaToolError


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("tool_func", "args", "expected_tool", "expected_payload"),
    [
        (
            messaging.wa_send_image,
            {
                "jid": "628123@s.whatsapp.net",
                "source": "data:image/png;base64,AAA",
                "caption": "Bukti pembayaran",
            },
            "send_image",
            {
                "jid": "628123@s.whatsapp.net",
                "source": "data:image/png;base64,AAA",
                "caption": "Bukti pembayaran",
            },
        ),
        (
            messaging.wa_send_image,
            {"jid": "628123@s.whatsapp.net", "source": "data:image/png;base64,AAA"},
            "send_image",
            {
                "jid": "628123@s.whatsapp.net",
                "source": "data:image/png;base64,AAA",
                "caption": "",
            },
        ),
        (
            messaging.wa_send_document,
            {
                "jid": "628123@s.whatsapp.net",
                "source": "/tmp/laporan.pdf",
                "filename": "laporan.pdf",
                "mimetype": "application/pdf",
            },
            "send_document",
            {
                "jid": "628123@s.whatsapp.net",
                "source": "/tmp/laporan.pdf",
                "filename": "laporan.pdf",
                "mimetype": "application/pdf",
            },
        ),
        (
            messaging.wa_send_audio,
            {"jid": "628123@s.whatsapp.net", "source": "data:audio/ogg;base64,BBB"},
            "send_audio",
            {"jid": "628123@s.whatsapp.net", "source": "data:audio/ogg;base64,BBB"},
        ),
        (
            messaging.wa_send_ptt,
            {"jid": "628123@s.whatsapp.net", "source": "data:audio/ogg;base64,CCC"},
            "send_ptt",
            {"jid": "628123@s.whatsapp.net", "source": "data:audio/ogg;base64,CCC"},
        ),
        (
            messaging.wa_send_video,
            {
                "jid": "628123@s.whatsapp.net",
                "source": "data:video/mp4;base64,DDD",
                "caption": "Recap",
            },
            "send_video",
            {
                "jid": "628123@s.whatsapp.net",
                "source": "data:video/mp4;base64,DDD",
                "caption": "Recap",
            },
        ),
        (
            messaging.wa_send_sticker,
            {"jid": "628123@s.whatsapp.net", "source": "data:image/webp;base64,EEE"},
            "send_sticker",
            {"jid": "628123@s.whatsapp.net", "source": "data:image/webp;base64,EEE"},
        ),
    ],
)
async def test_send_media_forwards_to_wa_enggine(
    monkeypatch, tool_func, args, expected_tool, expected_payload
):
    calls = []

    async def fake_call(tool_name, payload):
        calls.append((tool_name, payload))
        return {"success": True}

    monkeypatch.setattr(messaging, "call_wa_tool", fake_call)

    result = await tool_func.ainvoke(args)

    assert result == f"✅ Pesan berhasil dikirim ke {args['jid']}"
    assert calls[0][0] == expected_tool
    assert calls[0][1] == expected_payload


@pytest.mark.asyncio
async def test_send_media_returns_friendly_error_on_wa_tool_error(monkeypatch):
    async def fake_call(tool_name, payload):
        raise WaToolError("bot not authorized to send media")

    monkeypatch.setattr(messaging, "call_wa_tool", fake_call)

    result = await messaging.wa_send_image.ainvoke(
        {"jid": "628123@s.whatsapp.net", "source": "data:image/png;base64,AAA"}
    )

    assert result.startswith("⚠️ Gagal")
    assert "Gagal" in result
