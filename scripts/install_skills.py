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

`--xninetzy-only` restricts the run to the Xninetzy-prefixed skills (the
canonical Xninetzy skill set) and, when combined with `--force-xninetzy`,
backs up any preexisting non-symlink directories in the target catalog and
replaces them with symlinks to the built-in source. This guarantees that
the owner-mode Xninetzy experience in opencode / claude / codex always
loads the current Xninetzy skill set rather than a stale mirror.
"""

import argparse
import os
import shutil
import sys
from datetime import UTC, datetime
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


def install(
    target_name: str,
    target_root: Path,
    skill_dirs: list[Path],
    *,
    backup_prefix: str = "",
) -> tuple[int, int, int]:
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
            if not backup_prefix:
                print(
                    f"  ! skip {target_name}/{skill_dir.name}: path exists and is not a symlink",
                    file=sys.stderr,
                )
                skipped += 1
                continue
            backup = target_root / f"{skill_dir.name}.{backup_prefix}.bak"
            if backup.exists():
                ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
                backup = target_root / f"{skill_dir.name}.{backup_prefix}.{ts}.bak"
            shutil.move(str(link_path), str(backup))
            print(f"  ↪ backed up {target_name}/{skill_dir.name} → {backup.name}")
            replaced += 1
        link_path.symlink_to(skill_dir)
        installed += 1
    return installed, replaced, skipped


def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "Install skills").splitlines()[0])
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
    parser.add_argument(
        "--xninetzy-only",
        action="store_true",
        help="only install skills whose name starts with `xninetzy-`.",
    )
    parser.add_argument(
        "--force-xninetzy",
        action="store_true",
        help="with --xninetzy-only: back up any preexisting non-symlink directory in the target and replace with the built-in symlink. Use when the harness catalog carries stale mirrors.",
    )
    args = parser.parse_args()

    targets = tuple(args.target) if args.target else resolve_targets()
    skills = discover_skills()
    if not skills:
        print(f"No skills found under {SKILL_SOURCE_ROOT}", file=sys.stderr)
        return 1
    if args.xninetzy_only:
        skills = [s for s in skills if s.name.startswith("xninetzy-")]
        if not skills:
            print("No xninetzy-* skills found.", file=sys.stderr)
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
        backup_prefix = "xninetzy" if args.force_xninetzy else ""
        installed, replaced, skipped = install(
            name,
            target_root,
            skills,
            backup_prefix=backup_prefix,
        )
        verb = "installed" if replaced == 0 and skipped == 0 else "synced"
        print(f"    {verb}: {installed} link(s){', replaced ' + str(replaced) if replaced else ''}{', skipped ' + str(skipped) if skipped else ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
