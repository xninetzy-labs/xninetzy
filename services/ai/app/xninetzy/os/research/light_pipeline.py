from __future__ import annotations

from datetime import datetime, timezone

from app.xninetzy.core.logging import logging
from app.xninetzy.os.research.actions.base import ResearchActionInput
from app.xninetzy.os.research.actions.registry import ResearchActionRegistry

logger = logging.getLogger(__name__)


async def collect_quick_sources(
    topic: str,
    limit: int = 3,
    *,
    include_youtube: bool = True,
    include_academic: bool = True,
) -> list[dict]:
    """Gather web + YouTube + academic sources for one query without a session."""
    collected_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    sources: list[dict] = []
    jobs: list[tuple[str, dict]] = [
        ("web_search", {"limit": limit}),
    ]
    if include_youtube:
        jobs.append(("youtube_search", {"limit": 2, "include_youtube": True}))
    if include_academic:
        jobs.append(("academic_search", {"include_academic": True, "limit": limit}))

    for name, config in jobs:
        action = ResearchActionRegistry.get(name)
        if not action:
            continue
        try:
            out = await action.execute(
                ResearchActionInput(
                    session_id=0, topic=topic, query=topic, mode="balanced", config=config
                )
            )
            for source in out.data.get("sources", []):
                source["collected_at"] = collected_at
                sources.append(source)
        except Exception as error:
            logger.warning("quick source %s failed for %s: %s", name, topic, error)
    return sources


def group_sources_by_type(sources: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for source in sources:
        kind = "youtube" if source.get("source_type") == "youtube" else (
            "academic" if source.get("source_type") == "academic" else "web"
        )
        grouped.setdefault(kind, []).append(source)
    return grouped
