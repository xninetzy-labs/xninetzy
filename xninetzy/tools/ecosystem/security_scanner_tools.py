from __future__ import annotations

import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from langchain_core.tools import tool

from xninetzy.core.config import expand_path, get_settings
from xninetzy.db.sqlite import connect, init_db
from xninetzy.ecosystem.scanners import adapters as adapters_mod
from xninetzy.ecosystem.scanners import lock as lock_mod
from xninetzy.ecosystem.scanners import runner
from xninetzy.ecosystem.scanners.hit import SEVERITY_ORDER, ScanHit, sanitize_raw_output
from xninetzy.os.security import findings_store
from xninetzy.tools.ecosystem.security_tools import (
    _check_scope,
    _file_scope_targets,
    _lab_hosts,
    _matches_scope,
    _normalize_target,
    _reserve_lab_budget,
    _root_in_file_scope,
    _resolve_repo_root,
)

_EXECUTOR = subprocess.run
ZAP_BASELINE_COST = 1500
SCHEMATHESIS_COST_PER_EXAMPLE = 20
DEFAULT_HIT_LIMIT = 100
_PERSIST_CONFIDENCE = 0.7
_SELF_ALIASES = frozenset({"", "self", "repo", "."})


def _dump(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False)


def _security_root() -> Path:
    return Path(expand_path(get_settings().UNTRACKED_OUTPUT_DIR)) / "security"


def _new_session(scope_token: str, tool_name: str) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    return _security_root() / scope_token / f"{stamp}-{tool_name}"


def _scoped_source(scope_token: str, root: str, sender_id: str, tool_name: str) -> tuple[Path | None, dict[str, Any] | None, str | None]:
    ok, record, reason = _check_scope(scope_token, sender_id)
    if not ok or not record:
        return None, None, _dump({"error": reason, "scope_token": scope_token})
    file_targets = _file_scope_targets(record)
    if not file_targets:
        return None, None, _dump({"error": f"scope tidak berisi target file:; {tool_name} butuh file-scope", "scope_token": scope_token})
    if root.strip() in _SELF_ALIASES:
        path = _resolve_repo_root(root)
    else:
        path = Path(root).expanduser()
        if not path.is_absolute() or not path.is_dir():
            return None, None, _dump({"error": "root harus direktori absolut yang ada", "root": root})
    if not _root_in_file_scope(path, file_targets):
        return None, None, _dump({"error": "root di luar scope file target", "repo_root": str(path.resolve()), "allowed": file_targets})
    return path.resolve(), record, None


def _summarize(hits: list[ScanHit]) -> dict[str, int]:
    counts = Counter(h.severity for h in hits)
    return {name: counts.get(name, 0) for name in sorted(SEVERITY_ORDER, key=SEVERITY_ORDER.get, reverse=True)}


def _persist(scope_token: str, hits: list[ScanHit]) -> dict[str, int]:
    init_db()
    outcome: Counter[str] = Counter()
    with connect() as conn:
        for hit in hits:
            _finding_id, result = findings_store.upsert_finding(
                conn,
                scope_token,
                fingerprint=hit.fingerprint,
                asset=hit.asset,
                location=f"{hit.location}:{hit.line}" if hit.line else hit.location,
                category=hit.category,
                title=f"{hit.tool}: {hit.rule}",
                evidence=hit.evidence,
                severity=hit.severity,
                confidence=_PERSIST_CONFIDENCE,
                reproduction=hit.tool,
            )
            outcome[result] += 1
    return {key: outcome.get(key, 0) for key in ("created", "seen", "reopened")}


def _run_adapter(
    scope_token: str,
    adapter: adapters_mod.Adapter,
    target_label: str,
    persist: bool,
    limit: int,
    session_dir: Path | None = None,
) -> tuple[dict[str, Any], list[ScanHit]]:
    lock = lock_mod.load_lock()
    version = str(lock["tools"].get(adapter.tool, {}).get("version", ""))
    session = session_dir or _new_session(scope_token, adapter.tool)
    result = runner.run(adapter.spec, session, executor=_EXECUTOR)
    if result.status != runner.STATUS_OK:
        findings_store.record_run(scope_token, adapter.tool, target_label, result.status, 0, {"detail": result.detail}, version)
        return {
            "tool": adapter.tool,
            "status": result.status,
            "detail": result.detail,
            "stderr": result.stderr,
            "scope_token": scope_token,
        }, []
    output_file = session / adapter.output_file
    if not output_file.exists():
        findings_store.record_run(scope_token, adapter.tool, target_label, runner.STATUS_FAILED, 0, {"detail": "output tidak ditemukan"}, version)
        return {"tool": adapter.tool, "status": runner.STATUS_FAILED, "detail": "output tidak ditemukan", "stderr": result.stderr}, []
    raw_text = output_file.read_text(encoding="utf-8", errors="replace")
    output_file.write_text(sanitize_raw_output(raw_text), encoding="utf-8")
    try:
        hits = adapter.parse(raw_text)
    except (ValueError, KeyError, TypeError) as exc:
        findings_store.record_run(scope_token, adapter.tool, target_label, runner.STATUS_FAILED, 0, {"detail": type(exc).__name__}, version)
        return {"tool": adapter.tool, "status": runner.STATUS_FAILED, "detail": f"output tidak dapat di-parse: {type(exc).__name__}"}, []
    hits.sort(key=lambda h: (-SEVERITY_ORDER.get(h.severity, 0), h.asset, h.line))
    persisted = _persist(scope_token, hits) if persist else None
    summary = _summarize(hits)
    findings_store.record_run(scope_token, adapter.tool, target_label, runner.STATUS_OK, len(hits), {"by_severity": summary}, version)
    bounded = max(1, min(int(limit), 500))
    payload: dict[str, Any] = {
        "tool": adapter.tool,
        "status": runner.STATUS_OK,
        "version": version,
        "scope_token": scope_token,
        "target": target_label,
        "hit_count": len(hits),
        "by_severity": summary,
        "truncated": len(hits) > bounded,
        "hits": [h.to_dict() for h in hits[:bounded]],
        "output_path": str(output_file),
    }
    if persisted is not None:
        payload["persisted"] = persisted
    return payload, hits


def _source_scanner(
    tool_name: str,
    scope_token: str,
    root: str,
    sender_id: str,
    persist: bool,
    limit: int,
    factory,
) -> str:
    source, _record, error = _scoped_source(scope_token, root, sender_id, tool_name)
    if error:
        return error
    try:
        adapter = factory(source)
    except ValueError as exc:
        return _dump({"error": str(exc), "tool": tool_name})
    payload, _hits = _run_adapter(scope_token, adapter, str(source), persist, limit)
    return _dump(payload)


@tool(description="Laporkan kesehatan scanner (READY/DEGRADED/MISSING/UNHEALTHY) dari security-tools.lock; pin=true menulis digest image lokal ke lock.")
def security_check_tools(pin: bool = False) -> str:
    lock = lock_mod.load_lock()
    pinned: dict[str, str] = {}
    if pin:
        pinned = lock_mod.pin_from_local(lock, _EXECUTOR)
        lock_mod.save_lock(lock)
    rows = lock_mod.check_all(lock, _EXECUTOR)
    counts = Counter(r.status for r in rows)
    return _dump({
        "lock_path": str(lock_mod.default_lock_path()),
        "summary": {name: counts.get(name, 0) for name in (lock_mod.READY, lock_mod.DEGRADED, lock_mod.MISSING, lock_mod.UNHEALTHY)},
        "tools": [r.to_dict() for r in rows],
        "pinned": pinned,
    })


@tool(description="Jalankan Gitleaks (dir|git) pada repo dalam file-scope; secret selalu di-redact, hanya rule/file/line/hash prefix yang dilaporkan.")
def security_run_gitleaks(scope_token: str, root: str = "self", mode: str = "dir", persist: bool = False, limit: int = DEFAULT_HIT_LIMIT, sender_id: str = "") -> str:
    lock = lock_mod.load_lock()
    return _source_scanner("security_run_gitleaks", scope_token, root, sender_id, persist, limit,
                           lambda src: adapters_mod.gitleaks(lock, src, mode))


@tool(description="Jalankan Trivy (fs|config) pada repo dalam file-scope: kerentanan, secret, misconfiguration.")
def security_run_trivy(scope_token: str, root: str = "self", mode: str = "fs", persist: bool = False, limit: int = DEFAULT_HIT_LIMIT, sender_id: str = "") -> str:
    lock = lock_mod.load_lock()
    cache = _security_root() / "cache" / "trivy"
    return _source_scanner("security_run_trivy", scope_token, root, sender_id, persist, limit,
                           lambda src: adapters_mod.trivy(lock, src, mode, cache))


@tool(description="Jalankan OSV-Scanner rekursif pada lockfile repo dalam file-scope.")
def security_run_osv(scope_token: str, root: str = "self", persist: bool = False, limit: int = DEFAULT_HIT_LIMIT, sender_id: str = "") -> str:
    lock = lock_mod.load_lock()
    return _source_scanner("security_run_osv", scope_token, root, sender_id, persist, limit,
                           lambda src: adapters_mod.osv(lock, src))


@tool(description="Jalankan Semgrep dengan ruleset otomatis dari bahasa yang terdeteksi (atau rulesets eksplisit) pada repo dalam file-scope.")
def security_run_semgrep(scope_token: str, root: str = "self", rulesets: list[str] | None = None, persist: bool = False, limit: int = DEFAULT_HIT_LIMIT, sender_id: str = "") -> str:
    lock = lock_mod.load_lock()
    return _source_scanner("security_run_semgrep", scope_token, root, sender_id, persist, limit,
                           lambda src: adapters_mod.semgrep(lock, src, rulesets))


@tool(description="Buat SBOM CycloneDX dengan Syft lalu nilai kerentanannya dengan Grype untuk repo dalam file-scope.")
def security_sbom(scope_token: str, root: str = "self", persist: bool = False, limit: int = DEFAULT_HIT_LIMIT, sender_id: str = "") -> str:
    source, _record, error = _scoped_source(scope_token, root, sender_id, "security_sbom")
    if error:
        return error
    lock = lock_mod.load_lock()
    session = _new_session(scope_token, "sbom")
    syft_adapter = adapters_mod.Adapter("syft", adapters_mod.syft(lock, source), lambda _text: [], "sbom.cdx.json")
    syft_payload, _ = _run_adapter(scope_token, syft_adapter, str(source), False, 1, session)
    if syft_payload["status"] != runner.STATUS_OK:
        return _dump(syft_payload)
    from xninetzy.ecosystem.scanners.parsers import count_cyclonedx_components

    components = count_cyclonedx_components((session / "sbom.cdx.json").read_text(encoding="utf-8", errors="replace"))
    grype_adapter = adapters_mod.grype(lock, cache_dir=_security_root() / "cache" / "grype")
    payload, _hits = _run_adapter(scope_token, grype_adapter, str(source), persist, limit, session)
    payload["sbom_components"] = components
    payload["sbom_path"] = str(session / "sbom.cdx.json")
    return _dump(payload)


def _network_for(record: dict[str, Any]) -> str:
    return "host" if _lab_hosts(record) else "bridge"


@tool(description="Jalankan OWASP ZAP baseline (pasif) pada target dalam scope; mode api butuh scope owner_lab profile active dan schema OpenAPI.")
def security_run_zap(scope_token: str, target: str, mode: str = "baseline", schema_path: str = "", persist: bool = False, limit: int = DEFAULT_HIT_LIMIT, sender_id: str = "") -> str:
    ok, record, reason = _check_scope(scope_token, sender_id)
    if not ok or not record:
        return _dump({"error": reason, "scope_token": scope_token})
    if not _matches_scope(record, target):
        return _dump({"error": "target tidak termasuk scope"})
    if mode not in {"baseline", "api"}:
        return _dump({"error": "mode zap harus baseline atau api"})
    lab = record.get("lab") or {}
    if mode == "api" and (record.get("kind") != "owner_lab" or lab.get("profile") != "active"):
        return _dump({"error": "mode api butuh scope owner_lab dengan profile active"})
    try:
        canonical, _host, _port = _normalize_target(target, _lab_hosts(record))
    except ValueError as exc:
        return _dump({"error": str(exc)})
    if record.get("kind") == "owner_lab" and not _reserve_lab_budget(scope_token, ZAP_BASELINE_COST):
        return _dump({"error": "lab scope: request budget tidak cukup untuk ZAP", "required": ZAP_BASELINE_COST})
    lock = lock_mod.load_lock()
    try:
        adapter = adapters_mod.zap(lock, canonical, mode, _network_for(record), schema_path)
    except ValueError as exc:
        return _dump({"error": str(exc)})
    payload, _hits = _run_adapter(scope_token, adapter, canonical, persist, limit)
    return _dump(payload)


@tool(description="Jalankan Schemathesis pada schema OpenAPI/GraphQL target dalam scope dengan jumlah contoh terbatas.")
def security_run_schemathesis(scope_token: str, target: str, schema_url: str, max_examples: int = 25, persist: bool = False, limit: int = DEFAULT_HIT_LIMIT, sender_id: str = "") -> str:
    ok, record, reason = _check_scope(scope_token, sender_id)
    if not ok or not record:
        return _dump({"error": reason, "scope_token": scope_token})
    if not _matches_scope(record, target):
        return _dump({"error": "target tidak termasuk scope"})
    try:
        canonical, _host, _port = _normalize_target(target, _lab_hosts(record))
        schema_canonical, _h, _p = _normalize_target(schema_url, _lab_hosts(record))
    except ValueError as exc:
        return _dump({"error": str(exc)})
    if schema_canonical != canonical:
        return _dump({"error": "schema_url harus berada pada host:port target"})
    bounded = max(1, min(int(max_examples), 200))
    if record.get("kind") == "owner_lab" and not _reserve_lab_budget(scope_token, bounded * SCHEMATHESIS_COST_PER_EXAMPLE):
        return _dump({"error": "lab scope: request budget tidak cukup untuk Schemathesis"})
    lock = lock_mod.load_lock()
    adapter = adapters_mod.schemathesis(lock, schema_url, canonical, _network_for(record), bounded)
    payload, _hits = _run_adapter(scope_token, adapter, canonical, persist, limit)
    return _dump(payload)


@tool(description="Ubah status finding (open|fixed|accepted|false_positive) beserta fix_ref dan regression_test; scanner yang dijalankan ulang memperbarui last_seen alih-alih menduplikasi.")
def security_finding_update(scope_token: str, finding_id: int, status: str, fix_ref: str = "", regression_test: str = "", reason: str = "", sender_id: str = "") -> str:
    ok, _record, reason_text = _check_scope(scope_token, sender_id)
    if not ok:
        return _dump({"error": reason_text, "scope_token": scope_token})
    try:
        updated = findings_store.update_finding_status(scope_token, int(finding_id), status, fix_ref, regression_test, reason)
    except ValueError as exc:
        return _dump({"error": str(exc)})
    if updated is None:
        return _dump({"error": "finding tidak ditemukan dalam scope", "finding_id": finding_id})
    return _dump(updated)


def _finding_is_verified(finding: dict[str, Any]) -> bool:
    if finding.get("reproduction") == "runtime-proof":
        return True
    return finding.get("status") == "fixed" and bool(finding.get("fix_ref") or finding.get("regression_test"))


def render_report(scope_record: dict[str, Any], scope_token: str) -> str:
    findings = findings_store.list_findings(scope_token)
    runs = findings_store.list_runs(scope_token)
    lock = lock_mod.load_lock()
    now = datetime.now(timezone.utc).isoformat()
    lines = [
        f"# Security report {scope_token}",
        "",
        f"Generated: {now}",
        f"Scope kind: {scope_record.get('kind', 'standard')}",
        f"Targets: {', '.join(json.loads(scope_record.get('targets_json') or '[]'))}",
        f"Expires: {scope_record.get('expires_at') or 'n/a'}",
        "",
        "## Tools",
        "",
        "| Tool | Version | Runs | Last status |",
        "|---|---|---|---|",
    ]
    by_tool: dict[str, list[dict[str, Any]]] = {}
    for run in runs:
        by_tool.setdefault(run["tool"], []).append(run)
    for name in sorted(by_tool):
        version = next((r["version"] for r in reversed(by_tool[name]) if r["version"]), "") or str(lock["tools"].get(name, {}).get("version", ""))
        lines.append(f"| {name} | {version or 'n/a'} | {len(by_tool[name])} | {by_tool[name][-1]['status']} |")
    if not by_tool:
        lines.append("| none | | 0 | |")
    verified = [f for f in findings if f["status"] != "false_positive" and _finding_is_verified(f)]
    suspected = [f for f in findings if f["status"] == "open" and not _finding_is_verified(f)]
    closed = [f for f in findings if f["status"] in {"accepted", "false_positive"}]

    def block(title: str, items: list[dict[str, Any]]) -> None:
        lines.extend(["", f"## {title}", ""])
        if not items:
            lines.append("None.")
            return
        ordered = sorted(items, key=lambda f: (-SEVERITY_ORDER.get(str(f.get("severity")), 0), f["id"]))
        for f in ordered:
            fix = f" | fix: {f['fix_ref']}" if f.get("fix_ref") else ""
            test = f" | test: {f['regression_test']}" if f.get("regression_test") else ""
            seen = f" | seen {f['seen_count']}x" if f.get("seen_count") else ""
            lines.append(f"- [{f['severity']}] #{f['id']} {f['title']} ({f['asset']}) status={f['status']}{fix}{test}{seen}")

    block("Verified findings", verified)
    block("Suspected findings", suspected)
    block("Accepted and false positives", closed)
    lines.extend(["", "## Passed checks", ""])
    passed = [r for r in runs if r["status"] in {"OK", "pass"} and int(r["hit_count"]) == 0]
    if passed:
        lines.extend(f"- {r['tool']} on {r['target']}" for r in passed)
    else:
        lines.append("None recorded.")
    lines.extend(["", "## Limitations", ""])
    limitations = []
    for name, entries in sorted(by_tool.items()):
        bad = [e for e in entries if e["status"] in {"TOOL_MISSING", "TOOL_BLOCKED", "TIMEOUT", "FAILED"}]
        if bad:
            limitations.append(f"{name}: {bad[-1]['status']} on last failed run ({json.loads(bad[-1]['detail_json'] or '{}').get('detail', '')})")
    if any(r["tool"] == "sast-light" for r in runs):
        limitations.append("sast-light is regex-based, confidence 0.3; results are leads, not verified vulnerabilities")
    if any(r["tool"] == "dependency-inventory" for r in runs):
        limitations.append("dependency inventory carries no advisory data unless osv-scanner, trivy or grype ran")
    limitations.append("Findings marked suspected have no runtime proof or recorded fix")
    lines.extend(f"- {item}" for item in limitations)
    return "\n".join(lines) + "\n"


@tool(description="Render laporan Markdown (scope, tool+versi, finding verified/suspected, passed checks, keterbatasan) untuk satu scope; write=true menyimpan ke folder output security.")
def security_report(scope_token: str, write: bool = True, sender_id: str = "") -> str:
    ok, record, reason = _check_scope(scope_token, sender_id)
    if not ok or not record:
        return _dump({"error": reason, "scope_token": scope_token})
    markdown = render_report(record, scope_token)
    payload: dict[str, Any] = {"scope_token": scope_token, "markdown": markdown}
    if write:
        target = _security_root() / "reports"
        target.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path = target / f"{scope_token}-{stamp}.md"
        path.write_text(markdown, encoding="utf-8")
        payload["path"] = str(path)
    return _dump(payload)
