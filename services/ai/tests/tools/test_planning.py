from __future__ import annotations

from app.xninetzy.tools.internal.planning import (
    draft_workflow,
    generate_plan,
    idea_analysis,
    skill_discovery,
    task_breakdown,
)


def test_generate_plan_returns_structured_plan():
    result = generate_plan.invoke({"goal": "belajar FastAPI", "duration": "7 hari"})
    assert "Plan 7 hari: belajar FastAPI" in result
    assert "Fase 1" in result
    assert "Fase 2" in result
    assert "Fase 3" in result
    assert "Tips:" in result


def test_generate_plan_default_duration():
    result = generate_plan.invoke({"goal": "belajar FastAPI"})
    assert "Plan 7 hari" in result


def test_generate_plan_custom_duration():
    result = generate_plan.invoke({"goal": "selesaikan proyek X", "duration": "1 bulan"})
    assert "Plan 1 bulan: selesaikan proyek X" in result


def test_generate_plan_empty_goal_does_not_crash():
    result = generate_plan.invoke({"goal": ""})
    assert "Plan" in result


def test_task_breakdown_includes_deadline():
    result = task_breakdown.invoke({"task": "kerjakan tugas APSI", "deadline": "30 Juni"})
    assert "Task Breakdown: kerjakan tugas APSI" in result
    assert "Deadline: 30 Juni" in result or "Deadline:* 30 Juni" in result
    assert "Langkah-langkah:" in result


def test_task_breakdown_without_deadline():
    result = task_breakdown.invoke({"task": "kerjakan tugas APSI"})
    assert "Deadline:" not in result
    assert "Langkah-langkah:" in result


def test_task_breakdown_empty_task_does_not_crash():
    result = task_breakdown.invoke({"task": ""})
    assert "Task Breakdown:" in result


def test_draft_workflow_returns_draft():
    result = draft_workflow.invoke({"workflow_request": "otomasi backup catatan"})
    assert "Draft Workflow: otomasi backup catatan" in result
    assert "Trigger:" in result
    assert "Steps:" in result
    assert "Tools yang Mungkin Dibutuhkan:" in result


def test_idea_analysis_returns_analysis():
    result = idea_analysis.invoke({"idea": "aplikasi belajar bahasa"})
    assert "Analisis Ide" in result
    assert "Novelty" in result
    assert "MVP" in result


def test_skill_discovery_lists_capabilities():
    result = skill_discovery.invoke({})
    assert "Xninetzy AI" in result
    assert "Learning OS" in result
    assert "HEBAT" in result
    assert "Obsidian Vault" in result


def test_planning_tools_registered_in_registry():
    from app.xninetzy.tools.registry import get_all_tools

    names = {t.name for t in get_all_tools()}
    for name in (
        "generate_plan",
        "task_breakdown",
        "draft_workflow",
        "idea_analysis",
        "skill_discovery",
    ):
        assert name in names
