from __future__ import annotations

import json
from typing import Any

from langchain_core.tools import tool

from xninetzy.os.research.engine import (
    EngineConfig,
    advance_run,
    build_research_packet,
    discover_perspectives,
    generate_questions,
    start_run,
)
from xninetzy.schemas.research_packet import (
    RESEARCH_MODES,
    RESEARCH_RUN_STATES,
    SourceRecord,
    research_packet_to_dict,
    research_run_to_dict,
)
from xninetzy.tools.tool_results import to_tool_result


@tool
def research_storm_start(
    topic: str,
    mode: str = "STANDARD",
    source_mode: str = "hybrid",
    scope: str = "",
    depth: str = "STANDARD",
    audience: str = "",
    chat_id: str = "system",
    sender_id: str = "",
    idempotency_key: str = "",
) -> str:
    """Start a STORM-style deep research run. Returns the ResearchRun envelope.

    Args:
        topic: Research topic.
        mode: One of RESEARCH_MODES (QUICK_RESEARCH / STANDARD / DEEP_RESEARCH / LITERATURE_REVIEW / CORPUS_RESEARCH / TECHNICAL_RESEARCH / PROPOSAL_RESEARCH / CONSULTING_RESEARCH / INTERACTIVE_RESEARCH).
        source_mode: WEB_ONLY | CORPUS_ONLY | HYBRID.
        scope: Optional research scope.
        depth: Depth profile (QUICK | STANDARD | DEEP | EXTENSIVE).
        audience: Target audience.
        chat_id: Chat ID.
        sender_id: Owner principal.
        idempotency_key: Optional replay key.
    """
    from xninetzy.schemas.research_packet import ResearchBrief
    brief = ResearchBrief(topic=topic, scope=scope, target_audience=audience, depth=depth)
    run = start_run(topic=topic, brief=brief, mode=mode, source_mode=source_mode, owner_id=sender_id, project_id=chat_id)
    return to_tool_result(json.dumps({"research_run": research_run_to_dict(run), "valid_modes": sorted(RESEARCH_MODES)}, ensure_ascii=False))


@tool
def research_storm_perspectives(
    topic: str,
    scope: str = "",
    max_perspectives: int = 5,
) -> str:
    """Discover perspectives for a topic.

    Args:
        topic: Topic text.
        scope: Optional scope.
        max_perspectives: Cap on number of perspectives.
    """
    cfg = EngineConfig(max_perspectives=max_perspectives)
    from xninetzy.schemas.research_packet import ResearchBrief
    brief = ResearchBrief(topic=topic, scope=scope)
    perspectives = discover_perspectives(topic, brief, cfg)
    return to_tool_result(json.dumps({"perspectives": [{"id": p.perspective_id, "name": p.name, "description": p.description} for p in perspectives]}, ensure_ascii=False))


@tool
def research_storm_questions(
    topic: str,
    perspective_name: str = "",
    max_questions: int = 4,
) -> str:
    """Generate questions for a perspective.

    Args:
        topic: Research topic.
        perspective_name: Perspective name (defaults to first discovered).
        max_questions: Question cap.
    """
    from xninetzy.schemas.research_packet import ResearchPerspective
    cfg = EngineConfig(max_questions_per_perspective=max_questions)
    perspectives = discover_perspectives(topic, config=cfg)
    target = next((p for p in perspectives if p.name == perspective_name), perspectives[0])
    questions = generate_questions(target, topic, cfg)
    return to_tool_result(json.dumps({"perspective": target.name, "questions": [{"id": q.question_id, "type": q.question_type, "text": q.question} for q in questions]}, ensure_ascii=False))


@tool
def research_storm_advance(
    research_run_id: str,
    sources: list[dict[str, Any]],
) -> str:
    """Advance a research run through stages using provided sources.

    Args:
        research_run_id: Run ID returned from research_storm_start.
        sources: List of source dicts with at minimum {url, title, excerpt}.
    """
    srcs = [SourceRecord(url=s.get("url", ""), title=s.get("title", ""), excerpt=s.get("excerpt", ""), author=s.get("author", ""), published_at=s.get("published_at", "")) for s in sources]
    run = start_run(topic="")
    run.run_id = research_run_id
    run = advance_run(run, srcs)
    return to_tool_result(json.dumps({"research_run": research_run_to_dict(run)}, ensure_ascii=False))


@tool
def research_storm_packet(
    research_run_id: str,
    topic: str,
    sources: list[dict[str, Any]],
    scope: str = "",
) -> str:
    """Build a complete ResearchPacket (perspectives + questions + sources + evidence + claims + contradictions + gaps + outline).

    Args:
        research_run_id: Run ID.
        topic: Research topic.
        sources: List of source dicts {url, title, excerpt, author, published_at}.
        scope: Optional scope.
    """
    from xninetzy.schemas.research_packet import ResearchBrief, ResearchRun
    brief = ResearchBrief(topic=topic, scope=scope)
    run = ResearchRun(run_id=research_run_id, topic=topic, brief=brief)
    srcs = [SourceRecord(url=s.get("url", ""), title=s.get("title", ""), excerpt=s.get("excerpt", ""), author=s.get("author", ""), published_at=s.get("published_at", "")) for s in sources]
    packet = build_research_packet(run, srcs)
    return to_tool_result(json.dumps(research_packet_to_dict(packet), ensure_ascii=False))


@tool
def research_storm_capabilities() -> str:
    """Return STORM-style research capability snapshot."""
    return to_tool_result(json.dumps({
        "storm": True,
        "costorm": False,
        "web_research": True,
        "corpus_research": True,
        "vector_retrieval": True,
        "interactive_research": False,
        "mind_map": False,
        "states": sorted(RESEARCH_RUN_STATES),
        "modes": sorted(RESEARCH_MODES),
    }, ensure_ascii=False))


storm_tools = [
    research_storm_start,
    research_storm_perspectives,
    research_storm_questions,
    research_storm_advance,
    research_storm_packet,
    research_storm_capabilities,
]
