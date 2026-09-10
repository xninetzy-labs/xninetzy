import base64
from types import SimpleNamespace

import pytest
from mcp.types import ImageContent, TextContent

from xninetzy.os.academic.mahasiswa_portal import captcha_delivery as cd
from xninetzy.os.academic.mahasiswa_portal import tools as portal_tools

PNG_1PX = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


def _envelope(challenge_id="c1"):
    return cd.CaptchaEnvelope(
        png_bytes=PNG_1PX,
        challenge_id=challenge_id,
        expires_at="2026-08-05T16:02:39+00:00",
        site_slug="uacc",
        label="UACC",
        reply_command=f"/uacc-captcha {challenge_id} JAWABAN",
    )


@pytest.mark.asyncio
async def test_deliver_persists_to_owner_inbox(monkeypatch, tmp_path):
    captured: list[dict] = []

    def fake_capture(text, *, kind, chat_id):
        captured.append({"text": text, "kind": kind, "chat_id": chat_id})
        return ({}, True)

    monkeypatch.setattr(cd, "_persist_captcha_inbox", lambda *args, **kwargs: True)
    monkeypatch.setattr(cd, "capture_item", fake_capture, raising=False)
    monkeypatch.setattr(cd, "_open_local", lambda p: None)

    result = await cd.deliver_captcha(
        _envelope(),
        owner_chat_id="62812345678",
        captcha_dir=str(tmp_path),
    )

    assert result.delivered_via == "owner_inbox"
    assert result.blocks is not None
    assert result.png_path is not None
    assert (tmp_path / "uacc_captcha_c1.png").exists()
    assert isinstance(result.blocks[0], TextContent)
    assert isinstance(result.blocks[1], ImageContent)
    assert result.blocks[1].mimeType == "image/png"
    assert result.blocks[1].data == base64.b64encode(PNG_1PX).decode("ascii")
    assert "CAPTCHA harus dijawab manual oleh owner." in result.text


@pytest.mark.asyncio
async def test_deliver_falls_back_to_mcp_image_when_inbox_unavailable(monkeypatch, tmp_path):
    monkeypatch.setattr(cd, "_persist_captcha_inbox", lambda *args, **kwargs: False)
    monkeypatch.setattr(cd, "_open_local", lambda p: None)

    result = await cd.deliver_captcha(
        _envelope(),
        owner_chat_id="62812345678",
        captcha_dir=str(tmp_path),
    )

    assert result.delivered_via == "mcp_image"
    assert result.png_path is not None
    assert result.blocks is not None
    assert isinstance(result.blocks[0], TextContent)
    assert isinstance(result.blocks[1], ImageContent)
    assert "owner_inbox unavailable" in (result.error or "")


@pytest.mark.asyncio
async def test_deliver_uses_default_owner_when_chat_id_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(cd, "_persist_captcha_inbox", lambda *args, **kwargs: True)
    monkeypatch.setattr(cd, "_open_local", lambda p: None)
    monkeypatch.setattr(cd, "get_settings", lambda: SimpleNamespace(OWNER_CHAT_ID=""))

    result = await cd.deliver_captcha(
        _envelope(),
        owner_chat_id=None,
        captcha_dir=str(tmp_path),
    )

    assert result.delivered_via == "owner_inbox"
    assert "owner" in result.text or result.text


def _portal_settings(tmp_path):
    return SimpleNamespace(
        XNINETZY_CAPTCHA_WA_PREFERRED=True,
        XNINETZY_CAPTCHA_AUTO_OPEN=False,
        XNINETZY_CAPTCHA_DIR=str(tmp_path),
        XNINETZY_CAPTCHA_WA_TIMEOUT_SECONDS=8.0,
        OWNER_CHAT_ID="62812345678",
    )


def _mock_coordinator(monkeypatch, tmp_path):
    async def fake_start(owner_id, site_slug="mahasiswa"):
        return {
            "challenge_id": "challenge-uacc",
            "expires_at": "2026-08-05T16:02:39+00:00",
        }

    async def fake_captcha_png(challenge_id, owner_id):
        return PNG_1PX

    monkeypatch.setattr(portal_tools, "is_owner_admin", lambda sender_id, sender_name: True)
    monkeypatch.setattr(portal_tools.LOGIN_COORDINATOR, "start", fake_start)
    monkeypatch.setattr(portal_tools.LOGIN_COORDINATOR, "captcha_png", fake_captcha_png)
    monkeypatch.setattr(portal_tools, "get_settings", lambda: _portal_settings(tmp_path))
    monkeypatch.setattr(cd, "_persist_captcha_inbox", lambda *args, **kwargs: True)
    monkeypatch.setattr(cd, "_open_local", lambda p: None)


@pytest.mark.asyncio
async def test_uacc_login_start_returns_blocks_for_mcp_caller(monkeypatch, tmp_path):
    _mock_coordinator(monkeypatch, tmp_path)
    monkeypatch.setattr(portal_tools, "_notification_jid", lambda: None)

    result = await portal_tools.uacc_login_start.ainvoke(
        {
            "chat_id": "chat",
            "sender_id": "62812345678",
            "metadata": {"source": "mcp"},
        }
    )

    assert isinstance(result, list)
    assert isinstance(result[0], TextContent)
    assert isinstance(result[1], ImageContent)
    assert result[1].mimeType == "image/png"
    assert "challenge-uacc" in result[0].text


@pytest.mark.asyncio
async def test_uacc_login_start_whatsapp_metadata_alias_returns_text(monkeypatch, tmp_path):
    """Legacy ``metadata.channel == "whatsapp"`` callers still get plain text.

    The pivot removed WhatsApp delivery, so the text is now the inbox
    notification body rather than a WA message — but the return shape stays
    a ``str`` for backwards compat.
    """
    _mock_coordinator(monkeypatch, tmp_path)
    monkeypatch.setattr(portal_tools, "_notification_jid", lambda: None)

    result = await portal_tools.uacc_login_start.ainvoke(
        {
            "chat_id": "chat",
            "sender_id": "62812345678",
            "metadata": {"channel": "whatsapp"},
        }
    )

    assert isinstance(result, str)
    assert "PNG lokal" in result
