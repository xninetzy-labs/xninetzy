from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from langchain_core.tools import tool

from xninetzy.core.config import expand_path, get_settings


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slugify(text: str) -> str:
    safe = [c.lower() if c.isalnum() else "-" for c in text.strip()]
    collapsed = "".join(safe).strip("-")
    while "--" in collapsed:
        collapsed = collapsed.replace("--", "-")
    return collapsed or f"doc-{uuid.uuid4().hex[:8]}"


def _resolve_root(subdir: str) -> Path:
    host_root = Path(expand_path(get_settings().OBSIDIAN_VAULT_HOST_PATH))
    target = host_root / subdir
    target.mkdir(parents=True, exist_ok=True)
    return target


def _render_frontmatter(fields: dict[str, Any]) -> str:
    lines = ["---"]
    for key, value in fields.items():
        if isinstance(value, (list, dict)):
            rendered = json.dumps(value, ensure_ascii=False, sort_keys=True)
        else:
            rendered = str(value)
        lines.append(f"{key}: {rendered}")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def _write_doc(subdir: str, slug: str, body: str, extension: str = "md") -> dict[str, Any]:
    root = _resolve_root(subdir)
    target = root / f"{slug}.{extension}"
    counter = 1
    while target.exists():
        target = root / f"{slug}-{counter}.{extension}"
        counter += 1
    target.write_text(body, encoding="utf-8")
    return {
        "path": str(target),
        "slug": target.stem,
        "bytes": target.stat().st_size,
    }


@tool
def adr_generate(
    title: str,
    context: str,
    decision: str,
    consequences: list[str] | None = None,
    alternatives: list[str] | None = None,
    status: str = "proposed",
    tags: list[str] | None = None,
    chat_id: str = "system",
    sender_id: str = "",
) -> str:
    """Generate Architecture Decision Record (ADR) Obsidian-ready.

    Args:
        title: Judul ADR.
        context: Konteks keputusan.
        decision: Keputusan akhir.
        consequences: Daftar konsekuensi.
        alternatives: Alternatif yang dipertimbangkan.
        status: proposed|accepted|superseded|rejected.
        tags: Tag Obsidian.
        chat_id: Chat ID.
        sender_id: Owner principal.
    """
    bounded_status = status.strip().lower()
    if bounded_status not in {"proposed", "accepted", "superseded", "rejected"}:
        bounded_status = "proposed"
    now = _now_iso()
    frontmatter = _render_frontmatter({
        "kind": "adr",
        "title": title,
        "status": bounded_status,
        "owner": sender_id or "system",
        "tags": sorted(set((tags or []) + ["adr"])),
        "created_at": now,
    })
    body = [
        frontmatter,
        f"# {title}",
        "",
        f"**Status:** {bounded_status}  ",
        f"**Owner:** {sender_id or 'system'}  ",
        f"**Created:** {now}",
        "",
        "## Context",
        "",
        context.strip(),
        "",
        "## Decision",
        "",
        decision.strip(),
        "",
    ]
    if alternatives:
        body.extend(["## Alternatives Considered", ""])
        for alt in alternatives:
            body.append(f"- {alt}")
        body.append("")
    if consequences:
        body.extend(["## Consequences", ""])
        for cs in consequences:
            body.append(f"- {cs}")
        body.append("")
    full_body = "\n".join(body)
    slug = f"adr-{_slugify(title)}"
    written = _write_doc("adr", slug, full_body)
    return json.dumps({
        "kind": "adr",
        "title": title,
        "status": bounded_status,
        "path": written["path"],
        "owner": sender_id,
    }, ensure_ascii=False)


@tool
def implementation_record(
    title: str,
    summary: str,
    scope: str,
    steps: list[str] | None = None,
    tests: list[str] | None = None,
    risks: list[str] | None = None,
    related_artifacts: list[str] | None = None,
    tags: list[str] | None = None,
    chat_id: str = "system",
    sender_id: str = "",
) -> str:
    """Generate implementation record (Obsidian-ready).

    Args:
        title: Judul record.
        summary: Ringkasan singkat.
        scope: Ruang lingkup perubahan.
        steps: Daftar langkah eksekusi.
        tests: Daftar test/verifikasi.
        risks: Daftar risiko.
        related_artifacts: Path artifact terkait.
        tags: Tag Obsidian.
        chat_id: Chat ID.
        sender_id: Owner principal.
    """
    now = _now_iso()
    frontmatter = _render_frontmatter({
        "kind": "implementation_record",
        "title": title,
        "scope": scope,
        "owner": sender_id or "system",
        "tags": sorted(set((tags or []) + ["implementation"])),
        "created_at": now,
    })
    body = [
        frontmatter,
        f"# {title}",
        "",
        f"**Owner:** {sender_id or 'system'}  ",
        f"**Scope:** {scope}  ",
        f"**Created:** {now}",
        "",
        "## Summary",
        "",
        summary.strip(),
        "",
    ]
    if steps:
        body.extend(["## Implementation Steps", ""])
        for i, step in enumerate(steps, 1):
            body.append(f"{i}. {step}")
        body.append("")
    if tests:
        body.extend(["## Verification", ""])
        for t in tests:
            body.append(f"- {t}")
        body.append("")
    if risks:
        body.extend(["## Risks", ""])
        for r in risks:
            body.append(f"- {r}")
        body.append("")
    if related_artifacts:
        body.extend(["## Related Artifacts", ""])
        for ra in related_artifacts:
            body.append(f"- {ra}")
        body.append("")
    slug = f"impl-{_slugify(title)}"
    written = _write_doc("implementations", slug, "\n".join(body))
    return json.dumps({
        "kind": "implementation_record",
        "title": title,
        "path": written["path"],
        "owner": sender_id,
    }, ensure_ascii=False)


@tool
def security_finding_record(
    title: str,
    asset: str,
    severity: str,
    category: str,
    evidence: str,
    impact: str = "",
    remediation: str = "",
    regression_test: str = "",
    scope_token: str = "",
    confidence: float = 0.0,
    tags: list[str] | None = None,
    chat_id: str = "system",
    sender_id: str = "",
) -> str:
    """Generate security finding record (Obsidian-ready).

    Args:
        title: Judul finding.
        asset: Aset terdampak.
        severity: critical|high|medium|low|info.
        category: Kategori (sqli, xss, ...).
        evidence: Bukti.
        impact: Dampak.
        remediation: Saran perbaikan.
        regression_test: Test untuk mencegah regresi.
        scope_token: Scope token jika terkait pentest authorized.
        confidence: Confidence 0-1.
        tags: Tag Obsidian.
        chat_id: Chat ID.
        sender_id: Owner principal.
    """
    bounded_sev = severity.strip().lower()
    if bounded_sev not in {"critical", "high", "medium", "low", "info"}:
        bounded_sev = "medium"
    bounded_conf = max(0.0, min(confidence, 1.0))
    now = _now_iso()
    finding_id = f"sec-{uuid.uuid4().hex[:12]}"
    frontmatter = _render_frontmatter({
        "kind": "security_finding",
        "finding_id": finding_id,
        "title": title,
        "asset": asset,
        "severity": bounded_sev,
        "category": category,
        "confidence": bounded_conf,
        "scope_token": scope_token,
        "owner": sender_id or "system",
        "tags": sorted(set((tags or []) + ["security", category.lower()])),
        "created_at": now,
    })
    body = [
        frontmatter,
        f"# {title}",
        "",
        f"**Asset:** {asset}  ",
        f"**Severity:** {bounded_sev}  ",
        f"**Confidence:** {bounded_conf}  ",
        f"**Scope Token:** {scope_token or 'n/a'}  ",
        f"**Owner:** {sender_id or 'system'}  ",
        f"**Created:** {now}",
        "",
        "## Evidence",
        "",
        evidence.strip(),
        "",
    ]
    if impact.strip():
        body.extend(["## Impact", "", impact.strip(), ""])
    if remediation.strip():
        body.extend(["## Remediation", "", remediation.strip(), ""])
    if regression_test.strip():
        body.extend(["## Regression Test", "", regression_test.strip(), ""])
    slug = f"finding-{bounded_sev}-{_slugify(title)}"
    written = _write_doc("security/findings", slug, "\n".join(body))
    return json.dumps({
        "kind": "security_finding",
        "finding_id": finding_id,
        "title": title,
        "severity": bounded_sev,
        "path": written["path"],
        "owner": sender_id,
    }, ensure_ascii=False)


@tool
def learning_record(
    topic: str,
    takeaway: str,
    context: str = "",
    references: list[str] | None = None,
    confidence: float = 0.0,
    tags: list[str] | None = None,
    chat_id: str = "system",
    sender_id: str = "",
) -> str:
    """Generate learning record (Obsidian-ready).

    Args:
        topic: Topik pembelajaran.
        takeaway: Insight utama.
        context: Konteks.
        references: Daftar referensi/URL.
        confidence: Confidence 0-1.
        tags: Tag Obsidian.
        chat_id: Chat ID.
        sender_id: Owner principal.
    """
    bounded_conf = max(0.0, min(confidence, 1.0))
    now = _now_iso()
    frontmatter = _render_frontmatter({
        "kind": "learning_record",
        "topic": topic,
        "confidence": bounded_conf,
        "owner": sender_id or "system",
        "tags": sorted(set((tags or []) + ["learning"])),
        "created_at": now,
    })
    body = [
        frontmatter,
        f"# {topic}",
        "",
        f"**Confidence:** {bounded_conf}  ",
        f"**Owner:** {sender_id or 'system'}  ",
        f"**Created:** {now}",
        "",
    ]
    if context.strip():
        body.extend(["## Context", "", context.strip(), ""])
    body.extend(["## Takeaway", "", takeaway.strip(), ""])
    if references:
        body.extend(["## References", ""])
        for ref in references:
            body.append(f"- {ref}")
        body.append("")
    slug = f"learn-{_slugify(topic)}"
    written = _write_doc("learning", slug, "\n".join(body))
    return json.dumps({
        "kind": "learning_record",
        "topic": topic,
        "path": written["path"],
        "owner": sender_id,
    }, ensure_ascii=False)
