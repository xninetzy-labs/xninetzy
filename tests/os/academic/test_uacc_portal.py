import pytest

from app.xninetzy.core.config import get_settings
from app.xninetzy.os.academic.mahasiswa_portal import tools as portal_tools
from app.xninetzy.os.academic.mahasiswa_portal.login_coordinator import (
    portal_login_config,
)
from app.xninetzy.os.web_analysis.sites import get_site


def test_uacc_site_definition_and_aliases():
    site = get_site("uacc")
    assert site.base_url == "https://uacc.unair.ac.id"
    assert site.login_path == "/mhs"
    assert get_site("sso").slug == "uacc"
    assert get_site("unairsatu.unair.ac.id").slug == "uacc"


def test_portal_login_config_defaults_to_cyber_campus():
    settings = get_settings()
    config = portal_login_config("mahasiswa", settings)
    assert config.base_url == "https://mahasiswa.unair.ac.id"
    assert config.label == "Cyber Campus"


def test_portal_login_config_resolves_uacc():
    settings = get_settings()
    config = portal_login_config("uacc", settings)
    assert config.base_url == "https://uacc.unair.ac.id"
    assert config.label == "UACC"
    assert config.credential_source in {"hebat", "cyber"}


@pytest.mark.asyncio
async def test_uacc_login_denies_non_admin_before_browser_start(monkeypatch):
    started = False

    async def fake_start(owner_id, site_slug="mahasiswa"):
        nonlocal started
        started = True
        return {}

    monkeypatch.setattr(portal_tools, "is_owner_admin", lambda sender_id, sender_name: False)
    monkeypatch.setattr(portal_tools.LOGIN_COORDINATOR, "start", fake_start)

    result = await portal_tools.uacc_login_start.ainvoke(
        {"chat_id": "chat", "sender_id": "stranger@s.whatsapp.net"}
    )

    assert result == "Login UACC hanya dapat dimulai oleh admin."
    assert started is False


@pytest.mark.asyncio
async def test_uacc_captcha_submit_denies_non_admin(monkeypatch):
    submitted = False

    async def fake_submit(challenge_id, owner_id, answer):
        nonlocal submitted
        submitted = True
        return {}

    monkeypatch.setattr(portal_tools, "is_owner_admin", lambda sender_id, sender_name: False)
    monkeypatch.setattr(portal_tools.LOGIN_COORDINATOR, "submit", fake_submit)

    result = await portal_tools.uacc_login_submit_captcha.ainvoke(
        {
            "challenge_id": "challenge",
            "captcha_answer": "8",
            "chat_id": "chat",
            "sender_id": "stranger@s.whatsapp.net",
        }
    )

    assert result == "Jawaban CAPTCHA hanya dapat dikirim oleh admin."
    assert submitted is False


@pytest.mark.asyncio
async def test_uacc_login_start_forwards_captcha_to_admin(monkeypatch):
    sent = {}

    async def fake_start(owner_id, site_slug="mahasiswa"):
        assert site_slug == "uacc"
        return {
            "challenge_id": "challenge-uacc",
            "expires_at": "2026-08-05T00:00:00+00:00",
        }

    async def fake_deliver_captcha(
        owner_id, challenge, site_slug="mahasiswa", label="Cyber Campus", metadata=None
    ):
        sent["site_slug"] = site_slug
        sent["label"] = label
        return "CAPTCHA UACC sudah dikirim"

    async def fake_captcha_png(challenge_id, owner_id):
        return b"png"

    monkeypatch.setattr(portal_tools, "is_owner_admin", lambda sender_id, sender_name: True)
    monkeypatch.setattr(portal_tools.LOGIN_COORDINATOR, "start", fake_start)
    monkeypatch.setattr(portal_tools, "_deliver_captcha", fake_deliver_captcha)
    monkeypatch.setattr(
        portal_tools.LOGIN_COORDINATOR,
        "captcha_png",
        fake_captcha_png,
    )

    result = await portal_tools.uacc_login_start.ainvoke(
        {"chat_id": "chat", "sender_id": "628123@s.whatsapp.net"}
    )

    assert sent == {"site_slug": "uacc", "label": "UACC"}
    assert result == "CAPTCHA UACC sudah dikirim"


@pytest.mark.asyncio
async def test_uacc_captcha_envelope_uses_uacc_command(monkeypatch):
    from app.xninetzy.os.academic.mahasiswa_portal import captcha_delivery as cd

    envelope = cd.build_envelope(
        {"challenge_id": "challenge-uacc", "expires_at": "2026-08-05T00:00:00+00:00"},
        b"png",
        site_slug="uacc",
        label="UACC",
    )

    assert envelope.reply_command == "/uacc-captcha challenge-uacc JAWABAN"
    assert "/captcha challenge-uacc JAWABAN" not in envelope.reply_command


@pytest.mark.asyncio
async def test_uacc_session_status_reports_local_session(monkeypatch):
    monkeypatch.setattr(portal_tools.SessionManager, "has_session", lambda self, slug: slug == "uacc")
    result = await portal_tools.uacc_session_status.ainvoke({})
    assert "Session UACC tersedia secara lokal" in result


def test_uacc_session_is_separate_from_cyber(monkeypatch):
    seen = []

    def fake_has_session(self, slug):
        seen.append(slug)
        return slug == "uacc"

    monkeypatch.setattr(portal_tools.SessionManager, "has_session", fake_has_session)
    has_uacc, _ = portal_tools._session_present("uacc")
    has_cyber, _ = portal_tools._session_present("mahasiswa")
    assert has_uacc is True
    assert has_cyber is False
    assert seen == ["uacc", "mahasiswa"]


@pytest.mark.asyncio
async def test_uacc_logout_only_clears_uacc_session(monkeypatch):
    cleared = []

    def fake_clear(self, slug):
        cleared.append(slug)
        return True

    monkeypatch.setattr(portal_tools.SessionManager, "clear_session", fake_clear)
    result = await portal_tools.uacc_logout.ainvoke({})
    assert cleared == ["uacc"]
    assert "Session UACC dihapus" in result
