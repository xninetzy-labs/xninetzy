from __future__ import annotations

import re
from pathlib import Path

import pytest

from xninetzy.tools.registry import get_tool_names

SKILLS_ROOT = Path(__file__).resolve().parents[2] / ".agents" / "skills"
SECURITY_SKILLS = ("xninetzy-security-testing", "api-security")
TOOL_REF = re.compile(r"\bsecurity_[a-z0-9_]+\b(?!\.(?:json|md|ya?ml|txt|py))")
PLANNED_TOOLS = frozenset({"security_execute", "security_findings"})


def _markdown_files() -> list[Path]:
    files: list[Path] = []
    for skill in SECURITY_SKILLS:
        files.extend(sorted((SKILLS_ROOT / skill).rglob("*.md")))
    return files


def test_security_skill_files_exist():
    assert _markdown_files()


def test_workflow_references_only_registered_tools():
    workflow = SKILLS_ROOT / "xninetzy-security-testing" / "references" / "workflow.md"
    registered = set(get_tool_names())
    unknown = sorted({m for m in TOOL_REF.findall(workflow.read_text(encoding="utf-8")) if m not in registered})
    assert unknown == []


@pytest.mark.parametrize("path", _markdown_files(), ids=lambda p: str(p.relative_to(SKILLS_ROOT)))
def test_security_skill_tool_references_are_registered_or_declared_planned(path):
    registered = set(get_tool_names())
    referenced = set(TOOL_REF.findall(path.read_text(encoding="utf-8")))
    undeclared = sorted(referenced - registered - PLANNED_TOOLS)
    assert undeclared == []


def test_planned_tools_are_not_silently_registered():
    assert PLANNED_TOOLS.isdisjoint(set(get_tool_names()))
