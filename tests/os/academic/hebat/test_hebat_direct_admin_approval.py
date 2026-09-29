from __future__ import annotations

import pytest

from xninetzy.os.academic.hebat import tools as hebat_tools


@pytest.fixture()
def direct_admin_stubs(monkeypatch, tmp_path):
    upload_file = tmp_path / "tugas.pdf"
    upload_file.write_bytes(b"%PDF-1.4 dummy content")

    calls = {"uploaded": 0, "approval_requested": 0}

    monkeypatch.setattr(
        hebat_tools, "_resolve_activity_cmid",
        lambda ident, activity_type=None: ("7", "https://h/mod/assign/view.php?id=7"),
    )
    monkeypatch.setattr(hebat_tools, "cmid_to_activity_id", lambda cmid: 42)
    monkeypatch.setattr(hebat_tools, "_find_submission_by_idempotency", lambda key: None)
    monkeypatch.setattr(hebat_tools, "create_submission", lambda **kw: 1)
    monkeypatch.setattr(hebat_tools, "generate_token", lambda: "HBT-TESTTOKEN")
    monkeypatch.setattr(hebat_tools, "update_submission_status", lambda *a, **k: None)

    def _fake_request_approval(*args, **kwargs):
        calls["approval_requested"] += 1
        return 4242

    monkeypatch.setattr(hebat_tools, "request_approval", _fake_request_approval)

    async def _fake_upload(**kwargs):
        calls["uploaded"] += 1
        return {"status": "uploaded", "verification_text": "ok", "error": None}

    monkeypatch.setattr(hebat_tools, "upload_submission_via_playwright", _fake_upload)
    return upload_file, calls


@pytest.mark.asyncio
async def test_direct_admin_default_principal_requires_approval(direct_admin_stubs, monkeypatch):
    upload_file, calls = direct_admin_stubs
    monkeypatch.setattr(hebat_tools, "_is_owner_chat", lambda *a, **k: False)
    result = await hebat_tools.hebat_upload_submission.ainvoke(
        {
            "chat_id": "mcp:local-owner",
            "direct_file_path": str(upload_file),
            "direct_assignment_cmid": "7",
        }
    )
    assert "membutuhkan approval" in result
    assert calls["uploaded"] == 0
    assert calls["approval_requested"] == 1


@pytest.mark.asyncio
async def test_direct_admin_admin_substring_cannot_bypass(direct_admin_stubs, monkeypatch):
    upload_file, calls = direct_admin_stubs
    monkeypatch.setattr(hebat_tools, "_is_owner_chat", lambda *a, **k: False)
    for spoof in ("admin-evil", "local-x", "some-owner", "system"):
        result = await hebat_tools.hebat_upload_submission.ainvoke(
            {
                "chat_id": spoof,
                "direct_file_path": str(upload_file),
                "direct_assignment_cmid": "7",
            }
        )
        assert "membutuhkan approval" in result, spoof
    assert calls["uploaded"] == 0


@pytest.mark.asyncio
async def test_direct_admin_verified_owner_may_upload(direct_admin_stubs, monkeypatch):
    upload_file, calls = direct_admin_stubs
    monkeypatch.setattr(hebat_tools, "_is_owner_chat", lambda *a, **k: True)
    result = await hebat_tools.hebat_upload_submission.ainvoke(
        {
            "chat_id": "628123456789@chat.local",
            "direct_file_path": str(upload_file),
            "direct_assignment_cmid": "7",
        }
    )
    assert calls["uploaded"] == 1
    assert "Berhasil upload" in result
