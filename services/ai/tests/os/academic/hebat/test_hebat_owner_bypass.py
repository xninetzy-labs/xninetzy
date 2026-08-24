from __future__ import annotations

from app.xninetzy.os.academic.hebat import tools
from app.xninetzy.os.academic.hebat.tools import _is_owner_chat


def _patch_owners(monkeypatch, jids: tuple[str, ...]) -> None:
    monkeypatch.setattr(tools, "configured_owner_jids", lambda: frozenset(jids))


def test_owner_chat_matches_full_jid(monkeypatch):
    _patch_owners(monkeypatch, ("628123456789@s.whatsapp.net",))
    assert _is_owner_chat("628123456789@s.whatsapp.net")


def test_owner_chat_matches_bare_number_via_normalization(monkeypatch):
    _patch_owners(monkeypatch, ("628123456789@s.whatsapp.net",))
    assert _is_owner_chat("628123456789")


def test_owner_chat_checks_any_candidate(monkeypatch):
    _patch_owners(monkeypatch, ("628123456789@s.whatsapp.net",))
    assert _is_owner_chat("628999@s.whatsapp.net", "628123456789")


def test_non_owner_chat_rejected(monkeypatch):
    _patch_owners(monkeypatch, ("628123456789@s.whatsapp.net",))
    assert not _is_owner_chat("628999888777@s.whatsapp.net")


def test_empty_candidates_rejected(monkeypatch):
    _patch_owners(monkeypatch, ("628123456789@s.whatsapp.net",))
    assert not _is_owner_chat(None, "")
