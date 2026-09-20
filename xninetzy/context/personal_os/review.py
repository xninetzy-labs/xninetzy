from __future__ import annotations

from xninetzy.context.personal_os.models import (
    ProjectStatus,
    ReviewRun,
    _now,
    new_review_id,
)
from xninetzy.context.personal_os.service import get_personal_os


def generate_review(period: str = "weekly") -> ReviewRun:
    os_ = get_personal_os()
    active = os_.list_projects(status=ProjectStatus.ACTIVE)
    open_loops = os_.list_open_loops()
    stalled = tuple(p.project_id for p in active if os_.stall_project(p.project_id))
    recommendations: list[str] = []
    if stalled:
        recommendations.append(
            f"{len(stalled)} active project(s) inactive >= 14 days — review next_action."
        )
    if len(open_loops) > 10:
        recommendations.append(
            f"{len(open_loops)} open loops; prioritize top-importance before adding more."
        )
    if len(active) > 5:
        recommendations.append(
            f"{len(active)} active projects; consider pausing low-priority ones."
        )
    if not recommendations:
        recommendations.append("No structural issues detected; continue cadence.")
    return ReviewRun(
        review_id=new_review_id(),
        period=period,
        generated_at=_now(),
        active_projects=tuple(p.project_id for p in active),
        open_loops=tuple(l.loop_id for l in open_loops),
        stalled_projects=stalled,
        recommendations=tuple(recommendations),
    )
