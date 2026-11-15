from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from xninetzy.core.config import get_settings
from xninetzy.db.migrations import run_migrations
from xninetzy.db.sqlite import connect, init_db
from xninetzy.os.hitl.approval_service import request_approval, _apply_status_decision
from xninetzy.os.policy.action_policy import ActionMode, RiskClass, evaluate_action


def test_policy_auto_for_read_and_draft(monkeypatch, tmp_path):
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "policy.sqlite3"))
    get_settings.cache_clear()
    init_db()
    run_migrations()

    assert evaluate_action("portal_grades").mode is ActionMode.AUTO
    assert evaluate_action("learning_prepare_plan").risk is RiskClass.DRAFT


def test_career_lookup_tools_classify_as_read():
    from xninetzy.os.policy.action_policy import classify_risk

    for action in (
        "career_find_similar_jobs",
        "career_find_alternative_titles",
        "career_find_hidden_jobs",
        "career_extract_requirements",
    ):
        assert classify_risk(action) is RiskClass.READ, f"{action} should be READ"


def test_career_analysis_tools_classify_as_draft():
    from xninetzy.os.policy.action_policy import classify_risk

    for action in (
        "career_skill_gap",
        "career_market_skill_trend",
        "career_salary_analysis",
        "career_company_research",
        "career_interview_prep",
        "career_resume_analysis",
    ):
        assert classify_risk(action) is RiskClass.DRAFT, f"{action} should be DRAFT"


def test_career_manifest_overrides_match_effective_risk():
    from xninetzy.os.policy.action_policy import classify_risk
    from xninetzy.tools.manifest import manifest_for

    for name in (
        "career_find_similar_jobs",
        "career_find_alternative_titles",
        "career_find_hidden_jobs",
        "career_extract_requirements",
        "career_skill_gap",
        "career_market_skill_trend",
        "career_salary_analysis",
        "career_company_research",
        "career_interview_prep",
        "career_resume_analysis",
    ):
        manifest = manifest_for(name)
        assert manifest.risk is classify_risk(name), (
            f"{name}: manifest risk {manifest.risk} must match classify_risk"
        )


def test_final_action_cannot_be_auto(monkeypatch):
    monkeypatch.setenv("ACTION_POLICY_DEFAULT_MODE", "auto")
    get_settings.cache_clear()

    decision = evaluate_action("portal_krs_final_submit", {"plan_id": "p1"})

    assert decision.mode is ActionMode.APPROVAL
    assert decision.requires_approval is True
    get_settings.cache_clear()


def test_manual_kill_switch_blocks_writes(monkeypatch):
    monkeypatch.setenv("ACTION_POLICY_KILL_SWITCH", "true")
    get_settings.cache_clear()

    decision = evaluate_action("hebat_upload_submission")

    assert decision.allowed is False
    assert decision.mode is ActionMode.MANUAL
    get_settings.cache_clear()


def test_approval_expires_and_double_approve_does_not_execute(monkeypatch, tmp_path):
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "approval.sqlite3"))
    get_settings.cache_clear()
    init_db()
    run_migrations()
    approval_id = request_approval(
        "chat",
        "sender",
        "read_only_test",
        "Read",
        "Read only",
        {"resource": "r"},
    )
    with connect() as conn:
        conn.execute(
            "UPDATE approval_requests SET expires_at=? WHERE id=?",
            (
                (datetime.now(ZoneInfo(get_settings().APP_TIMEZONE)) - timedelta(minutes=1)).isoformat(),
                approval_id,
            ),
        )
    ok, message = _apply_status_decision(approval_id, "approved")
    assert ok is False
    assert "kedaluwarsa" in message
    assert _apply_status_decision(approval_id, "approved")[0] is False
    get_settings.cache_clear()

def test_approved_action_hash_mismatch_is_rejected(monkeypatch, tmp_path):
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "hash.sqlite3"))
    get_settings.cache_clear()
    init_db()
    run_migrations()
    approval_id = request_approval(
        "chat",
        "sender",
        "read_only_hash_test",
        "Read",
        "Read only",
        {"resource": "r"},
    )
    with connect() as conn:
        conn.execute("UPDATE approval_requests SET status='approved' WHERE id=?", (approval_id,))
    from xninetzy.os.hitl.approval_service import validate_approval
    import pytest

    with pytest.raises(ValueError, match="tidak berlaku"):
        validate_approval(approval_id, "read_only_hash_test", "changed")
    get_settings.cache_clear()
