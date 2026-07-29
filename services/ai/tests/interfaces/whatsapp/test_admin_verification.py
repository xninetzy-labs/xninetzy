import pytest

from app.xninetzy.interfaces.whatsapp import messaging


def _media_content(media_type: str) -> dict:
    return {
        "ok": True,
        "media_type": media_type,
        "content_base64": "aGVsbG8=",
        "filename": "evidence.pdf",
        "mime_type": "application/pdf",
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("media_type", "expected_tool"),
    [("image", "send_image"), ("document", "send_document")],
)
async def test_forward_media_targets_fixed_admin(
    monkeypatch,
    media_type,
    expected_tool,
):
    calls = []
    approvals = []

    async def fake_download(chat_id, message_id):
        assert (chat_id, message_id) == ("source-chat", "MSG1")
        return {"ok": True}

    async def fake_content(chat_id, message_id):
        assert (chat_id, message_id) == ("source-chat", "MSG1")
        return _media_content(media_type)

    async def fake_call(tool_name, payload):
        calls.append((tool_name, payload))
        return {"success": True}

    async def fake_buttons(approval_id, text):
        approvals.append((approval_id, text))

    monkeypatch.setattr(messaging, "_admin_jid", lambda: "628123@s.whatsapp.net")
    monkeypatch.setattr(messaging, "download_media_message", fake_download)
    monkeypatch.setattr(messaging, "get_media_content", fake_content)
    monkeypatch.setattr(messaging, "call_wa_tool", fake_call)
    monkeypatch.setattr(messaging, "_send_admin_buttons", fake_buttons)

    result = await messaging.wa_forward_media_to_admin.ainvoke(
        {
            "message_id": "MSG1",
            "approval_id": 42,
            "caption": "Verifikasi bukti",
            "chat_id": "source-chat",
        }
    )

    assert result == "✅ Media dan tombol verifikasi dikirim ke admin."
    assert calls[0][0] == expected_tool
    assert calls[0][1]["jid"] == "628123@s.whatsapp.net"
    assert approvals == [(42, "Verifikasi bukti")]


@pytest.mark.asyncio
async def test_forward_media_rejects_unsupported_type(monkeypatch):
    async def fake_download(chat_id, message_id):
        return {"ok": True}

    async def fake_content(chat_id, message_id):
        return _media_content("audio")

    monkeypatch.setattr(messaging, "_admin_jid", lambda: "628123@s.whatsapp.net")
    monkeypatch.setattr(messaging, "download_media_message", fake_download)
    monkeypatch.setattr(messaging, "get_media_content", fake_content)

    result = await messaging.wa_forward_media_to_admin.ainvoke(
        {"message_id": "MSG1", "approval_id": 42, "chat_id": "source-chat"}
    )

    assert "hanya mendukung image dan document" in result
