from __future__ import annotations

from langchain_core.tools import tool

from xninetzy.context.personal_os import (
    ProjectStatus,
    SkillStatus,
    generate_review,
    get_personal_os,
)


@tool
def personal_project_create(
    title: str,
    objective: str = "",
    goal_id: int | None = None,
    next_action: str = "",
) -> dict:
    """Create a personal project with an explicit next_action. Projects without
    a next action are flagged by the review engine as stalled."""
    return get_personal_os().create_project(
        title=title,
        objective=objective,
        goal_id=goal_id,
        next_action=next_action,
    ).to_dict()


@tool
def personal_project_list(status: str | None = None) -> dict:
    """List personal projects. Status filter: active / paused / completed /
    abandoned. Default returns active only."""
    s = ProjectStatus(status) if status else ProjectStatus.ACTIVE
    return {
        "projects": [p.to_dict() for p in get_personal_os().list_projects(status=s)],
    }


@tool
def personal_project_status(
    project_id: str, status: str, next_action: str = ""
) -> dict:
    """Transition a project to a new status. ``status`` ∈ active / paused /
    completed / abandoned."""
    return get_personal_os().update_project_status(
        project_id,
        ProjectStatus(status),
        next_action=next_action,
    ).to_dict()


@tool
def personal_open_loop_create(
    title: str,
    description: str = "",
    importance: str = "medium",
    project_id: str | None = None,
    next_action: str = "",
) -> dict:
    """Track an unresolved item: pending response, waiting decision, or any
    thread that needs closure. Idempotent per (owner, title)."""
    return get_personal_os().open_loop(
        title=title,
        description=description,
        importance=importance,
        project_id=project_id,
        next_action=next_action,
    ).to_dict()


@tool
def personal_open_loop_list() -> dict:
    """List currently open loops with age_days and importance."""
    return {
        "loops": [l.to_dict() for l in get_personal_os().list_open_loops()],
    }


@tool
def personal_open_loop_resolve(loop_id: str) -> dict:
    """Mark an open loop as resolved. Returns the updated loop."""
    return get_personal_os().resolve_loop(loop_id).to_dict()


@tool
def personal_skill_register(name: str) -> dict:
    """Register a skill the user is tracking. Idempotent by name."""
    return get_personal_os().register_skill(name).to_dict()


@tool
def personal_skill_advance(name: str, status: str) -> dict:
    """Advance a skill to a target status. ``status`` ∈ unknown / exposed /
    practicing / applied / strong / stale. Increments evidence_count."""
    return get_personal_os().advance_skill(name, SkillStatus(status)).to_dict()


@tool
def personal_review_run(period: str = "weekly") -> dict:
    """Run a review for the given period (daily / weekly / monthly). Returns
    active_projects, open_loops, stalled_projects, recommendations."""
    return generate_review(period).to_dict()
