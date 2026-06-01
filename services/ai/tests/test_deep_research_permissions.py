from app.core.config import get_settings
from app.research.permissions import can_run_deep_research


def test_sender_name_misbahul_allowed(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("ADMIN_NAMES", "misbahul,misbahul muttaqin")
    allowed, reason = can_run_deep_research("x", "misbahul45", "private", {})
    assert allowed
    assert reason == "admin_name"


def test_admin_jid_allowed(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("ADMIN_JID", "628@s.whatsapp.net")
    allowed, reason = can_run_deep_research("628@s.whatsapp.net", "User", "private", {})
    assert allowed
    assert reason == "admin_jid"


def test_group_admin_allowed():
    allowed, reason = can_run_deep_research(
        "member@s.whatsapp.net",
        "User",
        "group",
        {"participantJid": "member@s.whatsapp.net", "groupAdmins": ["member@s.whatsapp.net"]},
    )
    assert allowed
    assert reason == "group_admin"


def test_regular_user_denied(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("ADMIN_JID", "owner@s.whatsapp.net")
    allowed, _ = can_run_deep_research("user@s.whatsapp.net", "Regular", "private", {})
    assert not allowed
