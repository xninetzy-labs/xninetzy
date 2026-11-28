from __future__ import annotations

import re
from pathlib import Path

from xninetzy.tools.registry import get_tool_names

SKILL_DIR = Path(__file__).resolve().parents[3] / ".agents" / "skills" / "kaggle"
TOOL_NAME = re.compile(r"\bkaggle_[a-z][a-z_]*[a-z]\b")
NON_TOOLS = frozenset({"kaggle_auth_required"})


def skill_text() -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in sorted(SKILL_DIR.rglob("*.md")))


def test_every_kaggle_name_in_the_skill_is_a_registered_tool() -> None:
    registered = set(get_tool_names())
    mentioned = set(TOOL_NAME.findall(skill_text())) - NON_TOOLS
    assert mentioned - registered == set()


def test_every_registered_kaggle_tool_is_documented_in_the_skill() -> None:
    documented = set(TOOL_NAME.findall(skill_text()))
    registered = {name for name in get_tool_names() if name.startswith("kaggle_")}
    assert registered - documented == set()


def test_skill_body_stays_inside_the_repository_size_budget() -> None:
    lines = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8").splitlines()
    assert len(lines) < 500
    assert "Detailed references" in "\n".join(lines)
    for reference in re.findall(r"`references/([\w.-]+\.md)`", "\n".join(lines)):
        assert (SKILL_DIR / "references" / reference).is_file()
