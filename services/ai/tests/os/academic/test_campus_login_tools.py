import pytest

from app.xninetzy.os.academic.mahasiswa_portal import tools as portal_tools


def test_owner_id_normalizes_whatsapp_device_suffix():
    assert (
        portal_tools._owner_id("628123:7@s.whatsapp.net", "unused")
        == "628123@s.whatsapp.net"
    )


@pytest.mark.asyncio
async def test_cyber_login_denies_non_admin_before_browser_start(monkeypatch):
    started = False

    async def fake_start(owner_id):
        nonlocal started
        started = True
        return {}

    monkeypatch.setattr(portal_tools, "is_owner_admin", lambda sender_id, sender_name: False)
    monkeypatch.setattr(portal_tools.LOGIN_COORDINATOR, "start", fake_start)

    result = await portal_tools.portal_login_start.ainvoke(
        {"chat_id": "chat", "sender_id": "stranger@s.whatsapp.net"}
    )

    assert result == "Login Cyber Campus hanya dapat dimulai oleh admin."
    assert started is False


@pytest.mark.asyncio
async def test_captcha_submit_denies_non_admin_before_challenge_access(monkeypatch):
    submitted = False

    async def fake_submit(challenge_id, owner_id, answer):
        nonlocal submitted
        submitted = True
        return {}

    monkeypatch.setattr(portal_tools, "is_owner_admin", lambda sender_id, sender_name: False)
    monkeypatch.setattr(portal_tools.LOGIN_COORDINATOR, "submit", fake_submit)

    result = await portal_tools.portal_login_submit_captcha.ainvoke(
        {
            "challenge_id": "challenge",
            "captcha_answer": "ABC9",
            "chat_id": "chat",
            "sender_id": "stranger@s.whatsapp.net",
        }
    )

    assert result == "Jawaban CAPTCHA hanya dapat dikirim oleh admin."
    assert submitted is False


@pytest.mark.asyncio
async def test_grade_submit_maps_allowed_owner_alias_to_admin_jid(monkeypatch):
    consumed_owner = ""

    async def fake_consume(challenge_id, owner_id, token):
        nonlocal consumed_owner
        consumed_owner = owner_id
        raise RuntimeError("stop after identity check")

    monkeypatch.setattr(portal_tools, "is_owner_admin", lambda sender_id, sender_name: True)
    monkeypatch.setattr(portal_tools, "_notification_jid", lambda: "628123@s.whatsapp.net")
    monkeypatch.setattr(portal_tools.GRADE_TOKEN_COORDINATOR, "consume", fake_consume)

    await portal_tools.submit_grade_token(
        "challenge",
        "12345",
        "145300000000000@lid",
    )

    assert consumed_owner == "628123@s.whatsapp.net"
