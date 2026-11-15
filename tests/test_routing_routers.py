from __future__ import annotations

from xninetzy.context.routing.routers import (
    MAX_OPTIONS_BY_LAYER,
    route_capability,
    route_domain,
    route_skill,
    route_task,
    route_tool,
    build_state_snapshot_for,
)
from xninetzy.context.registry.taxonomy import SEMANTIC_DOMAINS


def test_max_options_bounded_per_layer() -> None:
    assert MAX_OPTIONS_BY_LAYER["L2_domain"] <= 20
    assert MAX_OPTIONS_BY_LAYER["L3_skill"] <= 25
    assert MAX_OPTIONS_BY_LAYER["L4_task"] <= 20
    assert MAX_OPTIONS_BY_LAYER["L5_tool"] <= 25


def test_route_domain_returns_valid_shape() -> None:
    d = route_domain("submit assignment to HEBAT")
    assert d.layer == "L2_domain"
    assert d.shortlist_size >= len(SEMANTIC_DOMAINS) // 2


def test_route_skill_returns_valid_shape() -> None:
    d = route_skill(
        "summarize research papers",
        candidate_skills=("academic-writer", "research-critic", "literature-review-writer"),
    )
    assert d.layer == "L3_skill"
    assert d.shortlist_size <= 25


def test_route_task_returns_valid_shape() -> None:
    d = route_task("render the video", domain_set=("media",))
    assert d.layer == "L4_task"
    assert d.shortlist_size <= 20


def test_route_capability_returns_valid_shape() -> None:
    d = route_capability("extract entities", domain_set=("research",))
    assert d.layer == "L5_capability"


def test_route_tool_returns_valid_shape() -> None:
    d = route_tool(
        "submit HEBAT assignment",
        candidate_tools=("hebat_upload_submission", "hebat_get_assignment_detail", "video_render"),
    )
    assert d.layer == "L5_tool"
    assert d.shortlist_size <= 3


def test_state_snapshot_includes_chat_id() -> None:
    snap = build_state_snapshot_for(chat_id="test-chat", owner="hashed")
    assert snap.chat_id == "test-chat"
