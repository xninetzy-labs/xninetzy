from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DOCS_ROOT = REPO_ROOT / "apps" / "docs" / "src"


def _iter_doc_files() -> list[Path]:
    out: list[Path] = []
    for ext in ("*.md", "*.mdx", "*.astro"):
        out.extend((DOCS_ROOT / "pages").rglob(ext))
    return out


def _audit_snapshot() -> dict[str, int]:
    cmd = [
        sys.executable,
        "-m",
        "uv",
        "run",
        "--no-project",
        "--directory",
        str(REPO_ROOT),
        "python",
        "scripts/mcp_audit.py",
    ]
    proc = subprocess.run(
        [
            "uv",
            "run",
            "--no-project",
            "--directory",
            str(REPO_ROOT),
            "python",
            "scripts/mcp_audit.py",
            "--json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"audit failed: {proc.stderr}")
    import json

    return json.loads(proc.stdout)


def _tool_section(snapshot: dict) -> dict:
    return snapshot.get("tools", snapshot)


def test_no_stale_tool_total() -> None:
    snapshot = _audit_snapshot()
    total = _tool_section(snapshot)["total"]
    pattern = re.compile(r"\b(\d{2,4})\s+tools\b")
    stale_targets = {343, 259, 305, 7, 23, 12, 70, 68}
    seen: list[tuple[Path, int, str]] = []
    for path in _iter_doc_files():
        if path.name == "audit-report-2026-09-20.md":
            continue
        text = path.read_text(encoding="utf-8")
        for match in pattern.finditer(text):
            value = int(match.group(1))
            if value not in stale_targets:
                continue
            line = text[: match.start()].count("\n") + 1
            seen.append((path, line, match.group(0)))
    assert not seen, (
        "stale tool counts still present: "
        + ", ".join(f"{p}:{l}: {m}" for p, l, m in seen[:10])
    )


def test_audit_total_is_referenced() -> None:
    snapshot = _audit_snapshot()
    total = _tool_section(snapshot)["total"]
    found = False
    for path in _iter_doc_files():
        text = path.read_text(encoding="utf-8")
        if f"{total} tools" in text:
            found = True
            break
    assert found, f"audit total {total} not mentioned anywhere in docs"


def test_audit_feature_pack_matches_docs() -> None:
    snapshot = _audit_snapshot()
    packs = _tool_section(snapshot)["feature_pack"]
    pack_re = re.compile(
        r"Feature pack\s*=\s*`(?P<p>[a-zA-Z\-]+)`\s*\|\s*\**\s*(?P<n>\d+)"
    )
    docs_packs: dict[str, int] = {}
    text = (DOCS_ROOT / "pages" / "docs" / "mcp-system.md").read_text(
        encoding="utf-8"
    )
    for match in pack_re.finditer(text):
        docs_packs[match.group("p")] = int(match.group("n"))
    assert docs_packs, "feature pack table not found in mcp-system.md"
    for pack, count in packs.items():
        assert docs_packs.get(pack) == count, (
            f"feature pack {pack}: docs={docs_packs.get(pack)} "
            f"audit={count}"
        )


def test_audit_risk_matches_docs() -> None:
    snapshot = _audit_snapshot()
    risks = _tool_section(snapshot)["risk"]
    risk_re = re.compile(r"Risk\s*=\s*`(?P<r>\w+)`\s*\|\s*\**\s*(?P<n>\d+)")
    docs_risks: dict[str, int] = {}
    text = (DOCS_ROOT / "pages" / "docs" / "mcp-system.md").read_text(
        encoding="utf-8"
    )
    for match in risk_re.finditer(text):
        docs_risks[match.group("r")] = int(match.group("n"))
    assert docs_risks, "risk table not found in mcp-system.md"
    for risk, count in risks.items():
        assert docs_risks.get(risk) == count, (
            f"risk {risk}: docs={docs_risks.get(risk)} audit={count}"
        )
