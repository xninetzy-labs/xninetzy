from __future__ import annotations

"""Install every skill in `.agents/skills/` into supported agent harnesses.

Targets (env-driven via XNINETZY_SKILL_INSTALL_TARGETS, default: opencode,claude,codex):

* opencode  → ~/.config/opencode/skills/
* claude    → ~/.claude/skills/
* codex     → ~/.codex/skills/

Each skill is published by symlinking the source directory into the target
catalog. Symlinks keep a single source of truth: edits to `.agents/skills/`
show up in every harness without re-running this script.

Idempotent. Existing symlinks pointing to the right source are left alone;
stale links are replaced; regular dirs are skipped (refuse to clobber).
"""

import argparse
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_SOURCE_ROOT = REPO_ROOT / ".agents" / "skills"

DEFAULT_TARGETS: tuple[str, ...] = ("opencode", "claude", "codex")

TARGET_PATHS: dict[str, Path] = {
    "opencode": Path.home() / ".config" / "opencode" / "skills",
    "claude": Path.home() / ".claude" / "skills",
    "codex": Path.home() / ".codex" / "skills",
}


def resolve_targets() -> tuple[str, ...]:
    raw = os.environ.get("XNINETZY_SKILL_INSTALL_TARGETS", "").strip()
    if not raw:
        return DEFAULT_TARGETS
    return tuple(t.strip() for t in raw.split(",") if t.strip())


def discover_skills() -> list[Path]:
    if not SKILL_SOURCE_ROOT.is_dir():
        return []
    out: list[Path] = []
    for entry in sorted(SKILL_SOURCE_ROOT.iterdir()):
        if not entry.is_dir():
            continue
        if (entry / "SKILL.md").is_file():
            out.append(entry)
    return out


def install(target_name: str, target_root: Path, skill_dirs: list[Path]) -> tuple[int, int, int]:
    target_root.mkdir(parents=True, exist_ok=True)
    installed = replaced = skipped = 0
    for skill_dir in skill_dirs:
        link_path = target_root / skill_dir.name
        if link_path.is_symlink():
            try:
                current = link_path.resolve(strict=False)
            except OSError:
                current = None
            if current == skill_dir.resolve():
                installed += 1
                continue
            link_path.unlink()
            replaced += 1
        elif link_path.exists():
            print(
                f"  ! skip {target_name}/{skill_dir.name}: path exists and is not a symlink",
                file=sys.stderr,
            )
            skipped += 1
            continue
        link_path.symlink_to(skill_dir)
        installed += 1
    return installed, replaced, skipped


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--target",
        action="append",
        choices=sorted(TARGET_PATHS),
        help="harness to install into (repeatable). Defaults to env XNINETZY_SKILL_INSTALL_TARGETS or opencode,claude,codex.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="show what would happen without changing the filesystem",
    )
    args = parser.parse_args()

    targets = tuple(args.target) if args.target else resolve_targets()
    skills = discover_skills()
    if not skills:
        print(f"No skills found under {SKILL_SOURCE_ROOT}", file=sys.stderr)
        return 1
    print(f"Found {len(skills)} skill(s) under {SKILL_SOURCE_ROOT}")
    for name in targets:
        if name not in TARGET_PATHS:
            print(f"  ! unknown target '{name}'", file=sys.stderr)
            continue
        target_root = TARGET_PATHS[name]
        print(f"→ {name} ({target_root})")
        if args.dry_run:
            for skill in skills:
                print(f"    symlink {skill.name} → {target_root / skill.name}")
            continue
        installed, replaced, skipped = install(name, target_root, skills)
        verb = "installed" if replaced == 0 and skipped == 0 else "synced"
        print(f"    {verb}: {installed} link(s){', replaced ' + str(replaced) if replaced else ''}{', skipped ' + str(skipped) if skipped else ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
