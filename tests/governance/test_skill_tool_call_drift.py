from __future__ import annotations

import re
from pathlib import Path

from xninetzy.tools.registry import get_tool_names

SKILLS_ROOT = Path(__file__).resolve().parents[2] / ".agents" / "skills"
CALL = re.compile(r"(?<![\w.])([a-z][a-z0-9]*(?:_[a-z0-9]+)+)\(")
NON_TOOL_CALLS = frozenset({"process_large_pdf", "skill_reviews", "xninetzy_skill_get"})


def _registered() -> set[str]:
    return set(get_tool_names())


def _group_prefixes() -> set[str]:
    return {name.split("_", 1)[0] for name in _registered()}


def _skill_markdown() -> list[Path]:
    return sorted(SKILLS_ROOT.rglob("*.md"))


def test_skill_markdown_is_discovered():
    assert len(_skill_markdown()) > 100


def test_prefixed_tool_calls_in_skills_are_registered():
    registered = _registered()
    prefixes = _group_prefixes()
    unknown: dict[str, list[str]] = {}
    for path in _skill_markdown():
        for name in CALL.findall(path.read_text(encoding="utf-8", errors="replace")):
            if name in registered or name in NON_TOOL_CALLS or name.split("_", 1)[0] not in prefixes:
                continue
            unknown.setdefault(name, []).append(str(path.relative_to(SKILLS_ROOT)))
    assert unknown == {}


def test_bpmn_tools_are_documented_in_process_engineering_skill():
    text = (SKILLS_ROOT / "process-engineering" / "SKILL.md").read_text(encoding="utf-8")
    for name in ("process_bpmn_generate", "process_bpmn_validate", "process_bpmn_import", "process_bpmn_convert"):
        assert name in _registered()
        assert name in text
