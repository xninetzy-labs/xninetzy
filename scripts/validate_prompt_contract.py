"""Read-only integrity and known-conflict checks for versioned prompt sources.

These static checks are regression checks, not an instruction interpreter or
an authorization boundary. Host configuration is never installed or modified.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "docs/prompt-injection-core"
REQUIRED = (
    "CORE_PROMPT.md", "CORE_RULES.md", "CLI_SHARED_INSTRUCTIONS.md",
    "cli-overrides/codex-AGENTS.md", "cli-overrides/claude-CLAUDE.md",
    "cli-overrides/opencode-xninetzy-paksa.md",
)
KNOWN_CONFLICTS = (
    r"highest-priority block",
    r"no vendor default.{0,100}(?:override|weaken)",
    r"(?:invoke|call).{0,80}(?:FIRST|LAST).{0,80}every non-trivial",
    r"skip validation.{0,30}overrides? (?:authorization|approval)",
    r"xninetzy_\*.{0,15}(?:→|->).{0,8}(?:`?allow)",
)


def validate(root: Path) -> dict:
    root = root.resolve()
    failures: list[str] = []
    rows: list[dict] = []
    try:
        manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
        if not isinstance(manifest, dict) or not isinstance(manifest.get("files"), dict):
            raise ValueError("manifest must contain a files object")
        if manifest.get("version") != "2.2.0":
            failures.append("unsupported prompt contract version")
    except (OSError, ValueError) as exc:
        return {"ok": False, "files": [], "failures": [f"manifest: {type(exc).__name__}"]}

    for name in REQUIRED:
        if name not in manifest["files"]:
            failures.append(f"missing manifest entry: {name}")
    for name, metadata in manifest["files"].items():
        path = root / name
        if Path(name).is_absolute() or ".." in Path(name).parts or path.is_symlink():
            failures.append(f"unsafe path: {name}")
            continue
        if not path.resolve().is_relative_to(root):
            failures.append(f"unsafe path: {name}")
            continue
        try:
            raw = path.read_bytes()
            body = raw.decode("utf-8")
        except (OSError, UnicodeError):
            failures.append(f"missing or unreadable prompt: {name}")
            continue
        digest = hashlib.sha256(raw).hexdigest()
        if not isinstance(metadata, dict) or digest != metadata.get("sha256"):
            failures.append(f"hash mismatch: {name}")
        if not body.strip():
            failures.append(f"empty prompt: {name}")
        for pattern in KNOWN_CONFLICTS:
            if re.search(pattern, body, re.IGNORECASE):
                failures.append(f"known instruction conflict: {name}: {pattern}")
        if re.search(r"\{\{[^}]+\}\}|<YOUR_[A-Z_]+>", body):
            failures.append(f"unresolved placeholder: {name}")
        if name.startswith("cli-overrides/"):
            for reference in ("CORE_PROMPT.md", "CORE_RULES.md", "CLI_SHARED_INSTRUCTIONS.md"):
                if reference not in body:
                    failures.append(f"missing reference {reference}: {name}")
        if name == "CORE_RULES.md":
            for term in ("host platform", "authorization", "approval", "idempotency",
                         "untrusted evidence", "CAPTCHA", "OTP", "MFA",
                         "Workflow customization cannot bypass", "Never log or store secrets"):
                if term not in body:
                    failures.append(f"missing shared safety contract {term}: {name}")
        rows.append({"path": name, "sha256": digest, "bytes": len(raw),
                     "lines": len(body.splitlines()), "tokens": "NOT_MEASURED"})
    return {"ok": not failures, "version": manifest.get("version"),
            "files": rows, "failures": failures}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--installed", action="store_true", help="also compare owner files read-only")
    parser.add_argument("--home", type=Path, default=Path.home(), help="owner home for installed comparison")
    args = parser.parse_args()
    report = validate(args.root)
    if args.installed:
        locations = {
            "CORE_PROMPT.md": ".xninetzy/CORE_PROMPT.md",
            "CORE_RULES.md": ".xninetzy/CORE_RULES.md",
            "CLI_SHARED_INSTRUCTIONS.md": ".xninetzy/CLI_SHARED_INSTRUCTIONS.md",
            "cli-overrides/codex-AGENTS.md": ".codex/AGENTS.md",
            "cli-overrides/claude-CLAUDE.md": ".claude/CLAUDE.md",
            "cli-overrides/opencode-xninetzy-paksa.md": ".config/opencode/instructions/xninetzy-paksa.md",
        }
        report["installed"] = []
        for row in report["files"]:
            name = row["path"]
            if name not in locations:
                continue
            path = args.home / locations[name]
            try:
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                status = "match" if digest == row["sha256"] else "drift"
            except OSError:
                digest, status = None, "missing"
            report["installed"].append({"source": name, "status": status, "sha256": digest})
            if status != "match":
                report["failures"].append(f"installed {status}: {name}; review before installation")
        report["ok"] = not report["failures"]
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
