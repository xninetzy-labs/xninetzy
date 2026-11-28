from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from xninetzy.skills.registry import (
    FRONTMATTER_PATTERN,
    SkillValidationError,
    builtin_skill_dir,
    parse_skill_markdown,
)

ROOT = builtin_skill_dir()
LEGACY_SKILL_MIRRORS = {
    "exam_qa": "exam-qa",
    "process_engineering": "process-engineering",
}


def _iter_skill_files() -> list[Path]:
    return sorted(ROOT.glob("*/SKILL.md"))


def test_skill_catalog_yaml_parses() -> None:
    for sm in _iter_skill_files():
        match = FRONTMATTER_PATTERN.match(sm.read_text(encoding="utf-8"))
        assert match is not None, f"Missing frontmatter: {sm}"
        frontmatter = yaml.safe_load(match.group(1))
        assert isinstance(frontmatter, dict), f"Frontmatter must be a mapping: {sm}"
        assert frontmatter.get("name"), f"Missing name: {sm}"
        assert frontmatter.get("description"), f"Missing description: {sm}"


def test_canonical_skill_catalog_validates() -> None:
    broken: dict[str, str] = {}
    for sm in _iter_skill_files():
        if sm.parent.name in LEGACY_SKILL_MIRRORS:
            continue
        try:
            parse_skill_markdown(sm.read_text(encoding="utf-8"), path=sm, source="builtin")
        except (OSError, UnicodeError, SkillValidationError) as exc:
            broken[sm.parent.name] = str(exc)
    assert not broken, f"Invalid canonical skill definitions: {broken}"


@pytest.mark.parametrize("legacy,canonical", LEGACY_SKILL_MIRRORS.items())
def test_legacy_underscore_mirrors_are_rejected_with_canonical_replacements(
    legacy: str, canonical: str,
) -> None:
    legacy_path = ROOT / legacy / "SKILL.md"
    legacy_text = legacy_path.read_text(encoding="utf-8")
    with pytest.raises(
        SkillValidationError,
        match="name harus lowercase kebab-case|harus sama dengan folder",
    ):
        parse_skill_markdown(legacy_text, path=legacy_path, source="builtin")
    canonical_path = ROOT / canonical / "SKILL.md"
    definition, _ = parse_skill_markdown(
        canonical_path.read_text(encoding="utf-8"), path=canonical_path, source="builtin"
    )
    frontmatter = yaml.safe_load(FRONTMATTER_PATTERN.match(legacy_text).group(1))
    assert frontmatter["name"].replace("_", "-") == definition.name
    assert frontmatter["description"] == definition.description


def test_frontmatter_pattern_requires_trailing_newline() -> None:
    good = "---\nname: a\n---\nbody\n"
    assert FRONTMATTER_PATTERN.match(good) is not None
    bad_no_close = "---\nname: a\nbody\n"
    assert FRONTMATTER_PATTERN.match(bad_no_close) is None


def test_builtin_skill_dir_points_into_repo() -> None:
    assert ROOT.exists(), f"builtin skill dir does not exist: {ROOT}"
    assert ROOT.name == "skills"
    assert ROOT.parent.name == ".agents"
