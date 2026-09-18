from __future__ import annotations

from typing import Any

from xninetzy.os.policy.action_policy import RiskClass
from xninetzy.tools.manifest import manifest_for
from xninetzy.workflow.models import WorkflowAction, WorkflowPlan
from xninetzy.workflow.plan import build_workflow_plan

_RISK_TO_TIER: dict[str, int] = {
    RiskClass.READ.value: 0,
    RiskClass.DRAFT.value: 1,
    RiskClass.WRITE.value: 1,
    RiskClass.FINAL.value: 3,
}


def _known_tool_for_action(action_type: str) -> str | None:
    mapping: dict[str, str] = {
        "hebat_sync": "hebat_sync_courses",
        "hebat_course_detail": "hebat_get_course_detail",
        "hebat_assignment_detail": "hebat_get_assignment_detail",
        "hebat_download_materials": "hebat_download_material",
        "deep_research": "deep_research_topic",
        "web_search": "web_search",
        "youtube_search": "youtube_search",
        "paper_search": "research_search_papers",
        "knowledge_ingest": "knowledge_ingest_text",
        "roadmap_create": "learning_create_roadmap",
        "task_planning": "task_breakdown",
        "reminder_create": "reminder_create",
        "reminder_infer": "reminder_create",
        "reminder_list": "reminder_list",
        "reminder_cancel": "reminder_cancel",
        "obsidian_save": "obsidian_save_note",
        "memory_save": "memory_add",
        "final_synthesis": "daily_review_generate",
    }
    return mapping.get(action_type)


def tier_for_action(action: WorkflowAction) -> int:
    tool_name = _known_tool_for_action(action.type.value)
    if not tool_name:
        return 0
    manifest = manifest_for(tool_name)
    if manifest is None:
        return 0
    return _RISK_TO_TIER.get(manifest.risk.value, 0)


def tiers_for_plan(plan: WorkflowPlan) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for action in plan.actions:
        tool_name = _known_tool_for_action(action.type.value) or ""
        manifest = manifest_for(tool_name) if tool_name else None
        tier = _RISK_TO_TIER.get(manifest.risk.value, 0) if manifest else 0
        result[action.id] = {
            "tier": tier,
            "tool_name": tool_name,
            "risk_class": manifest.risk.value if manifest else "unknown",
            "requires_approval": manifest.requires_approval if manifest else False,
            "title": action.title,
        }
    return result


def finalize_class_for_plan(plan: WorkflowPlan) -> dict[str, int]:
    counts: dict[str, int] = {"tier_0": 0, "tier_1": 0, "tier_2": 0, "tier_3": 0}
    for action in plan.actions:
        tier = tier_for_action(action)
        key = f"tier_{tier}"
        counts[key] = counts.get(key, 0) + 1
    return counts


def final_step_ids(plan: WorkflowPlan) -> list[str]:
    return [
        action.id
        for action in plan.actions
        if tier_for_action(action) >= 3
    ]


async def build_tier_aware_plan(
    chat_id: str,
    user_message: str,
    context: dict | None = None,
) -> tuple[WorkflowPlan, dict[str, Any]]:
    plan = await build_workflow_plan(chat_id, user_message, context)
    tiers = tiers_for_plan(plan)
    counts = finalize_class_for_plan(plan)
    final_ids = final_step_ids(plan)
    summary = {
        "tiers": tiers,
        "counts": counts,
        "final_step_ids": final_ids,
        "requires_owner_approval": bool(final_ids),
    }
    return plan, summary
