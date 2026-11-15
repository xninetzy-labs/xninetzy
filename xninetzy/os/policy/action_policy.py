from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import StrEnum

from xninetzy.core.config import get_settings


class ActionMode(StrEnum):
    AUTO = "auto"
    APPROVAL = "approval"
    MANUAL = "manual"


class RiskClass(StrEnum):
    READ = "read"
    DRAFT = "draft"
    WRITE = "write"
    FINAL = "final"


@dataclass(frozen=True, slots=True)
class ActionPolicyDecision:
    action: str
    risk: RiskClass
    mode: ActionMode
    allowed: bool
    requires_approval: bool
    reason: str
    action_hash: str


_FINAL_ACTIONS = frozenset(
    {
        "portal_krs_final_submit",
        "portal_krs_war_execute",
        "portal_krs_war_arm",
        "hebat_submit_submission",
        "hebat_submit_submission_direct",
        "qa_submit_kuesioner",
        "tableau_publish_workbook",
    }
)
_READ_PREFIXES = ("read", "list", "get", "check", "search", "status")
_READ_ACTIONS = frozenset(
    {
        "portal_session_status",
        "portal_profile",
        "portal_academic_status",
        "portal_current_krs",
        "portal_schedule",
        "portal_grades",
        "portal_grade_changes",
        "portal_navigation",
        "portal_info",
        "portal_krs_capabilities",
        "portal_krs_war_status",
    }
)
_DRAFT_MARKERS = ("prepare", "plan", "draft", "preview", "dry_run", "analyze")
_RISK_OVERRIDES: dict[str, RiskClass] = {
    "career_find_similar_jobs": RiskClass.READ,
    "career_find_alternative_titles": RiskClass.READ,
    "career_find_hidden_jobs": RiskClass.READ,
    "career_extract_requirements": RiskClass.READ,
    "career_skill_gap": RiskClass.DRAFT,
    "career_market_skill_trend": RiskClass.DRAFT,
    "career_salary_analysis": RiskClass.DRAFT,
    "career_company_research": RiskClass.DRAFT,
    "career_interview_prep": RiskClass.DRAFT,
    "career_resume_analysis": RiskClass.DRAFT,
    "security_compose_review": RiskClass.READ,
    "security_nginx_review": RiskClass.READ,
    "security_role_paths": RiskClass.READ,
    "security_check_tools": RiskClass.READ,
    "scaling_review": RiskClass.READ,
    "perf_compare": RiskClass.READ,
    "perf_capacity": RiskClass.READ,
    "redis_review": RiskClass.READ,
    "postgres_review": RiskClass.READ,
    "security_authz_matrix": RiskClass.DRAFT,
    "perf_plan": RiskClass.DRAFT,
    "process_bpmn_validate": RiskClass.READ,
    "process_bpmn_import": RiskClass.READ,
    "process_bpmn_generate": RiskClass.WRITE,
    "process_bpmn_convert": RiskClass.WRITE,
}


def classify_risk(action: str) -> RiskClass:
    normalized = action.strip().lower()
    from xninetzy.tools.manifest import policy_catalog

    policy = policy_catalog().get(normalized)
    if policy is not None:
        return RiskClass(policy)
    if normalized == "learning_prepare_plan":
        return RiskClass.DRAFT
    override = _RISK_OVERRIDES.get(normalized)
    if override is not None:
        return override
    if normalized in _FINAL_ACTIONS:
        return RiskClass.FINAL
    if normalized in _READ_ACTIONS:
        return RiskClass.READ
    return RiskClass.FINAL


def _overrides() -> dict[str, ActionMode]:
    raw = get_settings().ACTION_POLICY_OVERRIDES
    result: dict[str, ActionMode] = {}
    for item in raw.split(","):
        key, separator, value = item.partition("=")
        if not separator:
            continue
        try:
            result[key.strip()] = ActionMode(value.strip().lower())
        except ValueError:
            continue
    return result


def action_hash(action: str, payload: dict | None = None) -> str:
    canonical = json.dumps(
        {"action": action, "payload": payload or {}},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def evaluate_action(action: str, payload: dict | None = None) -> ActionPolicyDecision:
    normalized = action.strip().lower()
    settings = get_settings()
    risk = classify_risk(normalized)
    if settings.ACTION_POLICY_KILL_SWITCH:
        mode = ActionMode.MANUAL
        reason = "Action policy kill switch aktif."
    elif risk in (RiskClass.READ, RiskClass.DRAFT):
        mode = ActionMode.AUTO
        reason = "Read dan draft tidak mengubah state eksternal."
    else:
        try:
            mode = ActionMode(settings.ACTION_POLICY_DEFAULT_MODE.lower())
        except ValueError:
            mode = ActionMode.APPROVAL
        mode = _overrides().get(normalized, mode)
        reason = "Write membutuhkan approval sesuai policy owner."
    if risk is RiskClass.FINAL and mode is ActionMode.AUTO:
        mode = ActionMode.APPROVAL
        reason = "Aksi final selalu membutuhkan approval owner."
    allowed = mode is not ActionMode.MANUAL
    return ActionPolicyDecision(
        action=normalized,
        risk=risk,
        mode=mode,
        allowed=allowed,
        requires_approval=mode is ActionMode.APPROVAL,
        reason=reason if allowed else "Aksi harus dilakukan manual oleh owner.",
        action_hash=action_hash(normalized, payload),
    )
