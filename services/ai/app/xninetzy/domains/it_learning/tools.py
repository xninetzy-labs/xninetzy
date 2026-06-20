"""Domain entry point for IT Learning tools.

Re-exports the existing roadmap tools (defined in ``roadmap_tools``) so callers
have a single domain-level import. No new tool logic here.
"""
from __future__ import annotations

from app.xninetzy.domains.it_learning.roadmap_tools import (
    learning_create_roadmap,
    learning_generate_today_plan,
    learning_list_roadmaps,
    learning_review_week,
)

IT_LEARNING_TOOL_NAMES = [
    "learning_create_roadmap",
    "learning_list_roadmaps",
    "learning_generate_today_plan",
    "learning_review_week",
]


def get_it_learning_tools():
    """Return the core IT Learning roadmap tools."""
    return [
        learning_create_roadmap,
        learning_list_roadmaps,
        learning_generate_today_plan,
        learning_review_week,
    ]


__all__ = [
    "learning_create_roadmap",
    "learning_list_roadmaps",
    "learning_generate_today_plan",
    "learning_review_week",
    "IT_LEARNING_TOOL_NAMES",
    "get_it_learning_tools",
]
