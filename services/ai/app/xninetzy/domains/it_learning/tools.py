"""Domain entry point for IT Learning tools.

Re-exports the existing roadmap tools (defined in ``roadmap_tools``) so callers
have a single domain-level import. No new tool logic here.
"""

from __future__ import annotations

from app.xninetzy.domains.it_learning.roadmap_tools import (
    learning_create_roadmap,
    learning_generate_today_plan,
    learning_get_study_progress,
    learning_list_roadmaps,
    learning_review_week,
)
from app.xninetzy.domains.it_learning.study_session import (
    learning_complete_study_session,
    learning_list_study_sessions,
    learning_start_study_session,
)

IT_LEARNING_TOOL_NAMES = [
    "learning_create_roadmap",
    "learning_list_roadmaps",
    "learning_generate_today_plan",
    "learning_get_study_progress",
    "learning_review_week",
    "learning_start_study_session",
    "learning_complete_study_session",
    "learning_list_study_sessions",
]


def get_it_learning_tools():
    """Return the core IT Learning roadmap tools."""
    return [
        learning_create_roadmap,
        learning_list_roadmaps,
        learning_generate_today_plan,
        learning_get_study_progress,
        learning_review_week,
        learning_start_study_session,
        learning_complete_study_session,
        learning_list_study_sessions,
    ]


__all__ = [
    "learning_create_roadmap",
    "learning_list_roadmaps",
    "learning_generate_today_plan",
    "learning_get_study_progress",
    "learning_review_week",
    "learning_start_study_session",
    "learning_complete_study_session",
    "learning_list_study_sessions",
    "IT_LEARNING_TOOL_NAMES",
    "get_it_learning_tools",
]
