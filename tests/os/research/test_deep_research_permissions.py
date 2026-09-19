from xninetzy.core.config import get_settings
from xninetzy.os.research.permissions import can_run_deep_research, is_owner_admin


def test_sender_name_misbahul_allowed(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("ADMIN_NAMES", "misbahul,misbahul muttaqin")
    allowed, reason = can_run_deep_research("x", "misbahul45", "private", {})
    assert allowed
    assert reason == "admin_name"


def test_admin_jid_allowed(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("ADMIN_JID", "628@chat.local")
    allowed, reason = can_run_deep_research("628@chat.local", "User", "private", {})
    assert allowed
    assert reason == "admin_jid"


def test_admin_device_jid_allowed(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("ADMIN_JID", "628@chat.local")
    assert is_owner_admin("628:7@chat.local", None)


def test_owner_lid_allowlist_allowed(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("ADMIN_JID", "628@chat.local")
    monkeypatch.setenv("OWNER_ALLOWED_JIDS", "991@lid,another@chat.local")
    assert is_owner_admin("991@lid", None)
    allowed, reason = can_run_deep_research("991@lid", "User", "private", {})
    assert allowed
    assert reason == "admin_jid"


def test_group_admin_allowed():
    allowed, reason = can_run_deep_research(
        "member@chat.local",
        "User",
        "group",
        {"participantJid": "member@chat.local", "groupAdmins": ["member@chat.local"]},
    )
    assert allowed
    assert reason == "group_admin"


def test_regular_user_denied(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("ADMIN_JID", "owner@chat.local")
    allowed, _ = can_run_deep_research("user@chat.local", "Regular", "private", {})
    assert not allowed
