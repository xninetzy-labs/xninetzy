import base64
from types import SimpleNamespace

import pytest
from mcp.types import ImageContent, TextContent

from app.xninetzy.interfaces.whatsapp.client import WaToolError
from app.xninetzy.os.academic.mahasiswa_portal import captcha_delivery as cd
from app.xninetzy.os.academic.mahasiswa_portal import tools as portal_tools

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
async def test_deliver_whatsapp_when_wa_healthy(monkeypatch, tmp_path):
    sent = []

    async def fake_send(jid, envelope):
        sent.append((jid, envelope.challenge_id))

    monkeypatch.setattr(cd, "_wa_healthcheck", lambda timeout: True)
    monkeypatch.setattr(cd, "_wa_send_image", fake_send)

    result = await cd.deliver_captcha(
        _envelope(),
        wa_jid="628123@s.whatsapp.net",
        captcha_dir=str(tmp_path),
    )

    assert result.delivered_via == "whatsapp"
    assert result.blocks is None
    assert result.png_path is None
    assert result.error is None
    assert sent == [("628123@s.whatsapp.net", "c1")]
    assert "CAPTCHA harus dijawab manual oleh owner." in result.text


@pytest.mark.asyncio
async def test_deliver_mcp_image_when_wa_down(monkeypatch, tmp_path):
    monkeypatch.setattr(cd, "_wa_healthcheck", lambda timeout: False)
    monkeypatch.setattr(cd, "_open_local", lambda p: None)

    result = await cd.deliver_captcha(
        _envelope(),
        wa_jid="628123@s.whatsapp.net",
        captcha_dir=str(tmp_path),
    )

    assert result.delivered_via == "mcp_image"
    assert result.png_path is not None
    assert (tmp_path / "uacc_captcha_c1.png").exists()
    assert result.blocks is not None
    assert isinstance(result.blocks[0], TextContent)
    assert isinstance(result.blocks[1], ImageContent)
    assert result.blocks[1].mimeType == "image/png"
    assert result.blocks[1].data == base64.b64encode(PNG_1PX).decode("ascii")
    assert "WA MCP tidak siap" in (result.error or "")


@pytest.mark.asyncio
async def test_deliver_mcp_image_when_wa_send_fails(monkeypatch, tmp_path):
    async def fake_send(jid, envelope):
        raise WaToolError("gagal kirim ke WhatsApp")

    monkeypatch.setattr(cd, "_wa_healthcheck", lambda timeout: True)
    monkeypatch.setattr(cd, "_wa_send_image", fake_send)
    monkeypatch.setattr(cd, "_open_local", lambda p: None)

    result = await cd.deliver_captcha(
        _envelope(),
        wa_jid="628123@s.whatsapp.net",
        captcha_dir=str(tmp_path),
    )

    assert result.delivered_via == "mcp_image"
    assert result.blocks is not None
    assert "gagal kirim ke WhatsApp" in (result.error or "")


@pytest.mark.asyncio
async def test_deliver_mcp_image_without_wa_jid(monkeypatch, tmp_path):
    monkeypatch.setattr(cd, "_open_local", lambda p: None)

    result = await cd.deliver_captcha(
        _envelope(),
        wa_jid=None,
        captcha_dir=str(tmp_path),
    )

    assert result.delivered_via == "mcp_image"
    assert "belum dikonfigurasi" in (result.error or "")


def _portal_settings(tmp_path):
    return SimpleNamespace(
        XNINETZY_CAPTCHA_WA_PREFERRED=True,
        XNINETZY_CAPTCHA_AUTO_OPEN=False,
        XNINETZY_CAPTCHA_DIR=str(tmp_path),
        XNINETZY_CAPTCHA_WA_TIMEOUT_SECONDS=8.0,
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
    monkeypatch.setattr(cd, "_open_local", lambda p: None)


@pytest.mark.asyncio
async def test_uacc_login_start_returns_blocks_for_mcp_caller(monkeypatch, tmp_path):
    _mock_coordinator(monkeypatch, tmp_path)
    monkeypatch.setattr(portal_tools, "_notification_jid", lambda: None)

    result = await portal_tools.uacc_login_start.ainvoke(
        {
            "chat_id": "chat",
            "sender_id": "628123@s.whatsapp.net",
            "metadata": {"source": "mcp"},
        }
    )

    assert isinstance(result, list)
    assert isinstance(result[0], TextContent)
    assert isinstance(result[1], ImageContent)
    assert result[1].mimeType == "image/png"
    assert "challenge-uacc" in result[0].text


@pytest.mark.asyncio
async def test_uacc_login_start_whatsapp_channel_gets_text_hint(monkeypatch, tmp_path):
    _mock_coordinator(monkeypatch, tmp_path)
    monkeypatch.setattr(portal_tools, "_notification_jid", lambda: None)
    monkeypatch.setattr(cd, "_wa_healthcheck", lambda timeout: False)

    result = await portal_tools.uacc_login_start.ainvoke(
        {
            "chat_id": "chat",
            "sender_id": "628123@s.whatsapp.net",
            "metadata": {"channel": "whatsapp"},
        }
    )

    assert isinstance(result, str)
    assert "PNG lokal" in result


@pytest.mark.asyncio
async def test_uacc_login_start_whatsapp_healthy_returns_text(monkeypatch, tmp_path):
    _mock_coordinator(monkeypatch, tmp_path)
    monkeypatch.setattr(portal_tools, "_notification_jid", lambda: "628123@s.whatsapp.net")

    async def fake_send(jid, envelope):
        pass

    monkeypatch.setattr(cd, "_wa_healthcheck", lambda timeout: True)
    monkeypatch.setattr(cd, "_wa_send_image", fake_send)

    result = await portal_tools.uacc_login_start.ainvoke(
        {
            "chat_id": "chat",
            "sender_id": "628123@s.whatsapp.net",
            "metadata": {"source": "mcp"},
        }
    )

    assert isinstance(result, str)
    assert "PNG lokal" not in result
