from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import ipaddress
import socket

import httpx
from langchain_core.tools import tool

from xninetzy.db.sqlite import connect, init_db
from xninetzy.db.idempotency import idempotent_call as _idempotent_call


DEFAULT_SCOPE_TTL_HOURS = 24
_SECURITY_HEADERS = (
    "strict-transport-security",
    "content-security-policy",
    "x-frame-options",
    "x-content-type-options",
    "referrer-policy",
    "permissions-policy",
    "x-xss-protection",
)
_PRIVATE_HOST_HINTS = {"localhost"}
_BLOCKED_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.0.0.0/24"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("198.18.0.0/15"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]
_REQUEST_TIMEOUT = 15.0


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _scope_seed(scope_token: str) -> str:
    return hashlib.sha256(f"xninetzy-scope:{scope_token}".encode()).hexdigest()[:16]


def _host_is_private(host: str) -> bool:
    lowered = host.lower().strip()
    if not lowered:
        return True
    if lowered in _PRIVATE_HOST_HINTS:
        return True
    try:
        addr = ipaddress.ip_address(lowered)
    except ValueError:
        return False
    return any(addr in network for network in _BLOCKED_NETWORKS)


def _private_ip_block_disabled() -> bool:
    import os

    return os.environ.get("XNINETZY_ALLOW_PRIVATE_TARGETS", "").strip().lower() in {
        "1", "true", "yes", "on",
    }


def _normalize_target(target: str) -> tuple[str, str, int]:
    parsed = urlparse(target.strip())
    if parsed.scheme.lower() in ("http", "https"):
        if not parsed.hostname:
            raise ValueError(f"target tidak valid: {target}")
        host = parsed.hostname.lower()
        if not _private_ip_block_disabled() and _host_is_private(host):
            raise ValueError(f"target tidak diizinkan (host private): {host}")
        port = parsed.port or (443 if parsed.scheme.lower() == "https" else 80)
        canonical = f"{parsed.scheme.lower()}://{host}:{port}"
        return canonical, host, port
    if parsed.scheme.lower() == "file":
        path = parsed.path or parsed.netloc
        if path.startswith("//"):
            path = path[1:]
        canonical = f"file://{path}"
        return canonical, path, 0
    raise ValueError(f"target tidak valid (scheme harus http/https/file): {target}")


def _ensure_db() -> None:
    init_db()


@tool
def security_scope(
    targets: list[str],
    rationale: str = "",
    ttl_hours: int = DEFAULT_SCOPE_TTL_HOURS,
    approved_by: str = "",
    sender_id: str = "",
    idempotency_key: str = "",
) -> str:
    """Daftarkan target ke scope token untuk audit keamanan resmi.

    Args:
        targets: Daftar host atau URL (maks 32).
        rationale: Alasan persetujuan (wajib non-kosong).
        ttl_hours: Durasi scope (1-720 jam, default 24).
        approved_by: Owner principal yang menyetujui.
        sender_id: Owner principal (dari context).
        idempotency_key: Kunci opsional.
    """
    if not targets:
        return json.dumps({"error": "targets kosong"}, ensure_ascii=False)
    if not rationale.strip():
        return json.dumps({"error": "rationale wajib diisi"}, ensure_ascii=False)
    bounded_ttl = max(1, min(ttl_hours, 720))
    bounded_targets = targets[:32]
    targets_truncated = len(targets) > 32

    canonical_targets: list[str] = []
    for target in bounded_targets:
        try:
            canonical, _host, _port = _normalize_target(target)
        except ValueError as exc:
            return json.dumps({"error": str(exc), "target": target}, ensure_ascii=False)
        if canonical in canonical_targets:
            continue
        canonical_targets.append(canonical)

    def _do() -> str:
        scope_token = "sec-" + uuid.uuid4().hex[:24]
        now = datetime.now(timezone.utc)
        expires = now + timedelta(hours=bounded_ttl)
        _ensure_db()
        with connect() as conn:
            conn.execute(
                """
                INSERT INTO security_scopes
                  (scope_token, owner, targets_json, rationale,
                   expires_at, approved_at, approved_by, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    scope_token,
                    sender_id or approved_by or "system",
                    json.dumps(canonical_targets),
                    rationale,
                    expires.isoformat(),
                    _now_iso(),
                    approved_by,
                    _now_iso(),
                ),
            )
        payload = {
            "scope_token": scope_token,
            "owner": sender_id or approved_by or "system",
            "approved_by": approved_by,
            "rationale": rationale,
            "targets": canonical_targets,
            "target_count": len(canonical_targets),
            "targets_truncated": targets_truncated,
            "original_target_count": len(bounded_targets),
            "created_at": _now_iso(),
            "expires_at": expires.isoformat(),
            "ttl_hours": bounded_ttl,
        }
        return json.dumps(payload, ensure_ascii=False)

    return _idempotent_call(
        "security_scope", idempotency_key,
        {"targets": canonical_targets, "rationale": rationale, "ttl_hours": bounded_ttl},
        _do,
    )[0]


def _ssrf_safe_event_hook(request: httpx.Request) -> None:
    parsed = urlparse(str(request.url))
    if parsed.scheme.lower() not in ("http", "https"):
        raise httpx.HTTPError(f"redirect scheme not allowed: {parsed.scheme}")
    host = parsed.hostname or ""
    if _private_ip_block_disabled():
        return
    if _host_is_private(host):
        raise httpx.HTTPError(f"redirect target blocked (literal private ip): {host}")
    if host and not _looks_like_ip(host):
        try:
            infos = socket.getaddrinfo(host, None)
        except (socket.gaierror, OSError) as exc:
            raise httpx.HTTPError(f"redirect dns resolution failed: {exc}")
        for info in infos:
            try:
                resolved = ipaddress.ip_address(info[4][0])
            except (ValueError, IndexError):
                continue
            if any(resolved in network for network in _BLOCKED_NETWORKS):
                raise httpx.HTTPError(f"redirect resolved to private ip: {resolved}")


def _looks_like_ip(host: str) -> bool:
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        return False


def _check_scope(
    scope_token: str, sender_id: str | None = None
) -> tuple[bool, dict[str, Any] | None, str]:
    if not scope_token or not scope_token.startswith("sec-"):
        return False, None, "scope_token tidak valid"
    _ensure_db()
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM security_scopes WHERE scope_token=?", (scope_token,),
        ).fetchone()
    if not row:
        return False, None, "scope_token tidak ditemukan"
    record = dict(row)
    if sender_id:
        owner = (record.get("owner") or "").strip().lower()
        caller = (sender_id or "").strip().lower()
        if owner and caller and owner != caller:
            return False, record, "scope_token bukan milik caller"
        if not owner and caller:
            return False, record, "scope tanpa owner tidak bisa dipakai caller teridentifikasi"
    expires = record.get("expires_at")
    if expires:
        try:
            expiry_dt = datetime.fromisoformat(expires)
        except ValueError:
            expiry_dt = None
        if expiry_dt and expiry_dt < datetime.now(timezone.utc):
            return False, record, "scope sudah kadaluarsa"
    return True, record, "ok"


def _matches_scope(record: dict[str, Any], target: str) -> bool:
    try:
        canonical, _, _ = _normalize_target(target)
    except ValueError:
        return False
    targets = json.loads(record.get("targets_json") or "[]")
    return canonical in targets


def _matches_target(asset: str, target: str) -> bool:
    try:
        canonical, _, _ = _normalize_target(target)
    except ValueError:
        return False
    asset_norm = (asset or "").strip()
    if not asset_norm:
        return False
    try:
        asset_canonical, _, _ = _normalize_target(asset_norm)
        if asset_canonical == canonical:
            return True
    except ValueError:
        pass
    asset_lower = asset_norm.lower()
    if canonical.startswith("file://"):
        return asset_lower.startswith(canonical[len("file://"):])
    return asset_lower.endswith(canonical) or canonical.endswith(asset_lower)


def _target_kind(canonical: str) -> str:
    if canonical.startswith("file://"):
        return "file"
    if canonical.startswith(("http://", "https://")):
        return "http"
    return "unknown"


@tool
def security_assets(
    scope_token: str,
    target: str,
    limit: int = 200,
    sender_id: str = "",
) -> str:
    """Enumerasi aset publik dari target dalam scope (paths seed, headers, files).

    Args:
        scope_token: Token scope yang valid.
        target: URL target dalam scope.
        limit: Maks aset (cap 500).
        sender_id: Owner principal.
    """
    ok, record, reason = _check_scope(scope_token, sender_id)
    if not ok or not record:
        return json.dumps({"error": reason, "scope_token": scope_token}, ensure_ascii=False)
    if not _matches_scope(record, target):
        return json.dumps({"error": "target tidak termasuk scope"}, ensure_ascii=False)

    bounded_limit = max(1, min(limit, 500))
    try:
        canonical, host, _port = _normalize_target(target)
    except ValueError as exc:
        return json.dumps({"error": str(exc)}, ensure_ascii=False)
    headers = {"User-Agent": "Xninetzy-SecurityAssets/1.0"}
    seed_paths = ["/", "/robots.txt", "/sitemap.xml", "/.well-known/security.txt", "/favicon.ico"]
    assets: list[dict[str, Any]] = []
    try:
        with httpx.Client(
            timeout=_REQUEST_TIMEOUT,
            follow_redirects=True,
            headers=headers,
            event_hooks={"request": [_ssrf_safe_event_hook]},
        ) as client:
            for path in seed_paths:
                try:
                    response = client.get(f"{canonical}{path}")
                except httpx.HTTPError as exc:
                    assets.append({"path": path, "error": str(exc)})
                    continue
                assets.append({
                    "path": path,
                    "status": response.status_code,
                    "content_type": response.headers.get("content-type", ""),
                    "server": response.headers.get("server", ""),
                    "bytes": len(response.content),
                })
                if len(assets) >= bounded_limit:
                    break
    except httpx.HTTPError as exc:
        return json.dumps({"error": f"connect failed: {exc}"}, ensure_ascii=False)

    payload = {
        "scope_token": scope_token,
        "target": canonical,
        "host": host,
        "asset_count": len(assets),
        "truncated": len(assets) >= bounded_limit,
        "assets": assets,
    }
    return json.dumps(payload, ensure_ascii=False)


@tool
def security_headers(
    scope_token: str,
    target: str,
    sender_id: str = "",
) -> str:
    """Inspeksi header keamanan HTTP target dalam scope.

    Args:
        scope_token: Token scope.
        target: URL target.
        sender_id: Owner principal.
    """
    ok, record, reason = _check_scope(scope_token, sender_id)
    if not ok or not record:
        return json.dumps({"error": reason, "scope_token": scope_token}, ensure_ascii=False)
    if not _matches_scope(record, target):
        return json.dumps({"error": "target tidak termasuk scope"}, ensure_ascii=False)

    try:
        canonical, host, _port = _normalize_target(target)
    except ValueError as exc:
        return json.dumps({"error": str(exc)}, ensure_ascii=False)

    headers = {"User-Agent": "Xninetzy-SecurityHeaders/1.0"}
    try:
        with httpx.Client(
            timeout=_REQUEST_TIMEOUT,
            follow_redirects=True,
            headers=headers,
            event_hooks={"request": [_ssrf_safe_event_hook]},
        ) as client:
            response = client.get(canonical)
    except httpx.HTTPError as exc:
        return json.dumps({"error": f"connect failed: {exc}"}, ensure_ascii=False)

    response_headers = {k.lower(): v for k, v in response.headers.items()}
    present: list[dict[str, Any]] = []
    missing: list[str] = []
    for header in _SECURITY_HEADERS:
        if header in response_headers:
            present.append({"header": header, "value": response_headers[header][:300]})
        else:
            missing.append(header)
    cookies = response.headers.get_list("set-cookie") if hasattr(response.headers, "get_list") else []
    cookie_issues: list[str] = []
    for cookie in cookies:
        lowered = cookie.lower()
        if "secure" not in lowered:
            cookie_issues.append(f"missing Secure: {cookie[:60]}")
        if "httponly" not in lowered:
            cookie_issues.append(f"missing HttpOnly: {cookie[:60]}")
        if "samesite" not in lowered:
            cookie_issues.append(f"missing SameSite: {cookie[:60]}")

    payload = {
        "scope_token": scope_token,
        "target": canonical,
        "http_status": response.status_code,
        "present": present,
        "missing": missing,
        "cookie_issues": cookie_issues,
        "header_score": round((len(present) / len(_SECURITY_HEADERS)) * 100, 1),
    }
    return json.dumps(payload, ensure_ascii=False)


@tool
def security_api_inventory(
    scope_token: str,
    target: str,
    sender_id: str = "",
) -> str:
    """Inspeksi endpoint API umum (OpenAPI/Swagger/.well-known) dalam scope.

    Args:
        scope_token: Token scope.
        target: URL target.
        sender_id: Owner principal.
    """
    ok, record, reason = _check_scope(scope_token, sender_id)
    if not ok or not record:
        return json.dumps({"error": reason, "scope_token": scope_token}, ensure_ascii=False)
    if not _matches_scope(record, target):
        return json.dumps({"error": "target tidak termasuk scope"}, ensure_ascii=False)
    try:
        canonical, host, _port = _normalize_target(target)
    except ValueError as exc:
        return json.dumps({"error": str(exc)}, ensure_ascii=False)

    candidates = [
        "/.well-known/openapi.json",
        "/openapi.json",
        "/swagger.json",
        "/api/openapi.json",
        "/api/v1/openapi.json",
        "/v1/openapi.json",
        "/.well-known/api-catalog",
        "/api-docs",
        "/graphql",
    ]
    headers = {"User-Agent": "Xninetzy-SecurityApiInventory/1.0"}
    found: list[dict[str, Any]] = []
    try:
        with httpx.Client(
            timeout=_REQUEST_TIMEOUT,
            follow_redirects=True,
            headers=headers,
            event_hooks={"request": [_ssrf_safe_event_hook]},
        ) as client:
            for path in candidates:
                try:
                    response = client.get(f"{canonical}{path}")
                except httpx.HTTPError as exc:
                    found.append({"path": path, "error": str(exc)})
                    continue
                if response.status_code < 400 and response.content:
                    content_type = response.headers.get("content-type", "").casefold()
                    if "json" in content_type or path.endswith((".json", "-json")):
                        try:
                            body = response.json()
                            snippet = json.dumps(body)[:600]
                        except ValueError:
                            snippet = response.text[:200]
                        found.append({
                            "path": path,
                            "status": response.status_code,
                            "kind": "spec" if isinstance(body, dict) else "unknown",
                            "snippet": snippet,
                        })
    except httpx.HTTPError as exc:
        return json.dumps({"error": f"connect failed: {exc}"}, ensure_ascii=False)
    return json.dumps({
        "scope_token": scope_token,
        "target": canonical,
        "candidate_count": len(candidates),
        "found": found,
    }, ensure_ascii=False)


@tool
def security_sast(
    scope_token: str,
    root: str = "self",
    glob: str = "**/*.py",
    limit: int = 50,
    sender_id: str = "",
) -> str:
    """Jalankan pemindai SAST ringan pada kode (delegasi ke repo_risk).

    Args:
        scope_token: Token scope.
        root: Path atau alias repo (default self).
        glob: Pola file.
        limit: Maks finding.
        sender_id: Owner principal.
    """
    ok, record, reason = _check_scope(scope_token, sender_id)
    if not ok or not record:
        return json.dumps({"error": reason, "scope_token": scope_token}, ensure_ascii=False)
    targets = json.loads(record.get("targets_json") or "[]")
    file_targets = [
        t[len("file://"):] if t.startswith("file://") else t[len("file:"):]
        for t in targets if t.startswith("file:")
    ]
    file_targets = [p[1:] if p.startswith("//") else p for p in file_targets]
    if not file_targets:
        return json.dumps({
            "error": "scope tidak berisi target file:; security_sast butuh file-scope",
            "scope_token": scope_token,
        }, ensure_ascii=False)
    repo_root = str(_resolve_repo_root(root).resolve())
    if not any(repo_root.startswith(t) or t.startswith(repo_root) for t in file_targets):
        return json.dumps({
            "error": "root di luar scope file target",
            "scope_token": scope_token,
            "repo_root": repo_root,
            "allowed": file_targets,
        }, ensure_ascii=False)
    from xninetzy.tools.ecosystem.repo_tools import repo_risk
    result = repo_risk.invoke({"root": root, "glob": glob, "limit": limit, "sender_id": sender_id})
    return json.dumps({
        "scope_token": scope_token,
        "tool": "sast-light",
        "report": json.loads(result),
    }, ensure_ascii=False)


def _resolve_repo_root(root: str) -> Path:
    from xninetzy.tools.ecosystem.repo_tools import _resolve_root
    return _resolve_root(root)


@tool
def security_dependencies(
    scope_token: str,
    root: str = "self",
    sender_id: str = "",
) -> str:
    """Inventaris dependency dari pyproject + requirements dan peringatan versi.

    Args:
        scope_token: Token scope.
        root: Path atau alias repo.
        sender_id: Owner principal.
    """
    ok, record, reason = _check_scope(scope_token, sender_id)
    if not ok or not record:
        return json.dumps({"error": reason, "scope_token": scope_token}, ensure_ascii=False)
    targets = json.loads(record.get("targets_json") or "[]")
    file_targets = [
        t[len("file://"):] if t.startswith("file://") else t[len("file:"):]
        for t in targets if t.startswith("file:")
    ]
    file_targets = [p[1:] if p.startswith("//") else p for p in file_targets]
    if not file_targets:
        return json.dumps({
            "error": "scope tidak berisi target file:; security_dependencies butuh file-scope",
            "scope_token": scope_token,
        }, ensure_ascii=False)
    base = _resolve_repo_root(root).resolve()
    repo_root = str(base)
    if not any(repo_root.startswith(t) or t.startswith(repo_root) for t in file_targets):
        return json.dumps({
            "error": "root di luar scope file target",
            "scope_token": scope_token,
            "repo_root": repo_root,
            "allowed": file_targets,
        }, ensure_ascii=False)
    deps: list[dict[str, Any]] = []
    pyproject = base / "pyproject.toml"
    if pyproject.exists():
        try:
            text = pyproject.read_text(encoding="utf-8", errors="replace")
        except OSError:
            text = ""
        in_deps = False
        for raw in text.splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("[") and line.endswith("]"):
                in_deps = line.lower() in {"[dependencies]", "[project.dependencies]"}
                continue
            if in_deps and "=" in line:
                name = re.split(r"[<>=!~;\[]", line, maxsplit=1)[0].strip().strip("\"'")
                if name and not name.startswith("--"):
                    deps.append({"name": name, "version_hint": line.split("=", 1)[1][:40], "source": "pyproject.toml"})
    requirements = base / "requirements.txt"
    if requirements.exists():
        try:
            text = requirements.read_text(encoding="utf-8", errors="replace")
        except OSError:
            text = ""
        for raw in text.splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or line.startswith("-"):
                continue
            name = re.split(r"[<>=!~;\[]", line, maxsplit=1)[0].strip()
            if name:
                deps.append({"name": name, "version_hint": line, "source": "requirements.txt"})

    payload = {
        "scope_token": scope_token,
        "root": str(base),
        "dependency_count": len(deps),
        "dependencies": deps,
    }
    return json.dumps(payload, ensure_ascii=False)


@tool
def security_threat_model(
    scope_token: str,
    inventory_summary: str,
    threat_classes: list[str] | None = None,
    sender_id: str = "",
) -> str:
    """Skor ancaman terhadap inventory menggunakan kelas ancaman sederhana.

    Args:
        scope_token: Token scope.
        inventory_summary: Ringkasan inventaris (string JSON atau teks bebas).
        threat_classes: Daftar kelas ancaman (opsional).
        sender_id: Owner principal.
    """
    ok, record, reason = _check_scope(scope_token, sender_id)
    if not ok or not record:
        return json.dumps({"error": reason, "scope_token": scope_token}, ensure_ascii=False)

    classes = threat_classes or [
        "input_validation",
        "authn_z",
        "secrets_handling",
        "ssrf",
        "sql_injection",
        "xss",
        "csrf",
        "insecure_deserialization",
        "path_traversal",
        "race_condition",
        "weak_crypto",
        "tls_verification",
    ]
    summary_lower = inventory_summary.lower()
    matches: dict[str, int] = {}
    keywords = {
        "input_validation": ["input", "form", "request", "param", "body", "query"],
        "authn_z": ["auth", "login", "token", "jwt", "session", "permission", "role"],
        "secrets_handling": ["secret", "password", "api_key", "token", "credential"],
        "ssrf": ["url", "fetch", "httpx", "request", "external"],
        "sql_injection": ["sql", "database", "execute", "select", "insert", "update", "delete"],
        "xss": ["render", "html", "template", "frontend", "ui"],
        "csrf": ["form", "post", "session", "cookie"],
        "insecure_deserialization": ["pickle", "yaml", "load", "eval"],
        "path_traversal": ["open", "file", "path", "upload"],
        "race_condition": ["concurrent", "lock", "thread", "process", "queue"],
        "weak_crypto": ["md5", "sha1", "random"],
        "tls_verification": ["verify=false", "tls", "ssl"],
    }
    for cls in classes:
        keywords_for_cls = keywords.get(cls, [cls.replace("_", " ")])
        matches[cls] = sum(1 for kw in keywords_for_cls if kw in summary_lower)

    edges: list[dict[str, Any]] = []
    for cls, count in matches.items():
        if count > 0:
            severity = "high" if count >= 3 else "medium" if count >= 1 else "low"
            edges.append({
                "threat_class": cls,
                "signal_count": count,
                "severity": severity,
                "control_gap": "review needed",
            })
    edges.sort(key=lambda e: (-e["signal_count"], e["threat_class"]))
    return json.dumps({
        "scope_token": scope_token,
        "inventory_chars": len(inventory_summary),
        "threat_classes": classes,
        "edges": edges,
    }, ensure_ascii=False)


@tool
def security_validate_finding(
    scope_token: str,
    title: str,
    asset: str,
    location: str,
    category: str,
    evidence: str,
    impact: str = "",
    severity: str = "medium",
    confidence: float = 0.5,
    allow_runtime_proof: bool = False,
    sender_id: str = "",
    idempotency_key: str = "",
) -> str:
    """Validasi & persist SecurityFinding ke ledger (runtime proof hanya untuk lab).

    Args:
        scope_token: Token scope.
        title: Judul finding.
        asset: Aset (path modul atau URL).
        location: file:line atau endpoint.
        category: Kelas ancaman.
        evidence: Bukti reproduksi (path/cmd/output).
        impact: Dampak.
        severity: high|medium|low (default medium).
        confidence: 0.0-1.0.
        allow_runtime_proof: True hanya untuk lab terisolasi.
        sender_id: Owner principal.
        idempotency_key: Kunci opsional.
    """
    ok, record, reason = _check_scope(scope_token, sender_id)
    if not ok or not record:
        return json.dumps({"error": reason, "scope_token": scope_token}, ensure_ascii=False)
    if not title.strip() or not asset.strip():
        return json.dumps({"error": "title dan asset wajib diisi"}, ensure_ascii=False)
    bounded_confidence = max(0.0, min(confidence, 1.0))
    if severity not in {"high", "medium", "low", "critical", "info"}:
        return json.dumps({
            "error": f"severity tidak valid: {severity!r}; expected one of critical|high|medium|low|info",
        }, ensure_ascii=False)
    bounded_severity = severity
    reproduction = "static-evidence"
    if allow_runtime_proof:
        reproduction = "runtime-proof"

    def _do() -> str:
        _ensure_db()
        now = _now_iso()
        with connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO security_findings
                  (scope_token, asset, location, category, title, evidence,
                   precondition, reproduction, impact, confidence, severity,
                   status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    scope_token, asset, location, category, title, evidence,
                    "in-scope", reproduction, impact, bounded_confidence,
                    bounded_severity, "open", now, now,
                ),
            )
            finding_id = cur.lastrowid
        payload = {
            "id": finding_id,
            "scope_token": scope_token,
            "title": title,
            "asset": asset,
            "location": location,
            "category": category,
            "severity": bounded_severity,
            "confidence": bounded_confidence,
            "reproduction": reproduction,
            "status": "open",
        }
        return json.dumps(payload, ensure_ascii=False)

    return _idempotent_call(
        "security_validate_finding", idempotency_key,
        {"scope_token": scope_token, "title": title, "asset": asset},
        _do,
    )[0]


@tool
def security_regression(
    scope_token: str,
    finding_id: int,
    test_id: str = "",
    status: str = "proposed",
    sender_id: str = "",
) -> str:
    """Catat regression test untuk finding yang sudah dipatch.

    Args:
        scope_token: Token scope.
        finding_id: ID finding.
        test_id: Path atau nama test.
        status: proposed|passing|failing.
        sender_id: Owner principal.
    """
    ok, record, reason = _check_scope(scope_token, sender_id)
    if not ok or not record:
        return json.dumps({"error": reason, "scope_token": scope_token}, ensure_ascii=False)
    if status not in {"proposed", "passing", "failing"}:
        return json.dumps({
            "error": f"status tidak valid: {status!r}; expected one of proposed|passing|failing",
        }, ensure_ascii=False)
    bounded_status = status
    _ensure_db()
    with connect() as conn:
        cur = conn.execute(
            "UPDATE security_findings SET regression_test=?, status=?, updated_at=? WHERE id=? AND scope_token=?",
            (test_id or None, bounded_status, _now_iso(), finding_id, scope_token),
        )
        if cur.rowcount == 0:
            return json.dumps({"error": "finding tidak ditemukan dalam scope"}, ensure_ascii=False)
    return json.dumps({
        "scope_token": scope_token,
        "finding_id": finding_id,
        "test_id": test_id,
        "status": bounded_status,
    }, ensure_ascii=False)


def _correlate_key(hit: dict[str, Any]) -> tuple[str, str, str]:
    asset = str(hit.get("asset", "")).strip().lower()
    location = str(hit.get("location", "")).strip().lower()
    category = str(hit.get("category", "")).strip().lower()
    return (asset, location, category)


def _confidence_tier(scanner_count: int, agreement: float, max_severity: str) -> str:
    if scanner_count >= 3 and agreement >= 0.66:
        return "high"
    if scanner_count >= 2 and agreement >= 0.5 and max_severity in {"critical", "high"}:
        return "high"
    if scanner_count >= 2:
        return "medium"
    if scanner_count == 1 and max_severity in {"critical", "high"}:
        return "medium"
    return "low"


@tool
def security_correlate(
    hits: list[dict[str, Any]],
    persist: bool = False,
    scope_token: str = "",
    chat_id: str = "system",
    sender_id: str = "",
) -> str:
    """Korelasi hits multi-scanner jadi SecurityFinding unik dengan confidence tier.

    Args:
        hits: Daftar finding dari scanner berbeda. Wajib ada asset|location|category.
        persist: Jika True simpan hasil ke security_findings dalam scope.
        scope_token: Wajib jika persist=True.
        chat_id: Chat ID.
        sender_id: Owner principal.
    """
    if not hits:
        return json.dumps({"error": "hits kosong"}, ensure_ascii=False)
    if persist and not scope_token.strip():
        return json.dumps({"error": "scope_token wajib saat persist=True"}, ensure_ascii=False)

    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    skipped_invalid = 0
    for hit in hits[:256]:
        if not isinstance(hit, dict):
            skipped_invalid += 1
            continue
        key = _correlate_key(hit)
        groups.setdefault(key, []).append(hit)

    severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}
    unknown_severity_rank = -1
    now = _now_iso()
    findings: list[dict[str, Any]] = []
    persist_failures: list[str] = []

    if persist:
        _ensure_db()
        with connect() as conn:
            scope_row = conn.execute(
                "SELECT owner, targets_json, expires_at FROM security_scopes WHERE scope_token=?",
                (scope_token,),
            ).fetchone()
            if scope_row is None:
                return json.dumps({"error": "scope_token tidak ditemukan"}, ensure_ascii=False)
            targets = json.loads(scope_row["targets_json"] or "[]")
            for (asset, location, category), group in groups.items():
                if not any(_matches_target(asset, t) for t in targets):
                    persist_failures.append(f"asset out of scope: {asset}")
                    continue
                severities = [str(h.get("severity", "medium")).lower() for h in group]
                max_severity = max(severities, key=lambda s: severity_order.get(s, unknown_severity_rank)) if severities else "medium"
                confidences = [float(h.get("confidence", 0.5) or 0.0) for h in group]
                avg_conf = sum(confidences) / max(len(confidences), 1)
                scanners = sorted({str(h.get("scanner", "unknown")) for h in group})
                agreement = len(scanners) / max(len(group), 1)
                tier = _confidence_tier(len(scanners), agreement, max_severity)
                combined_confidence = round(min(avg_conf + (0.1 * (len(scanners) - 1)), 1.0), 4)
                evidence_lines = [
                    f"[{h.get('scanner', '?')}] {h.get('title', '')} ({h.get('confidence', 0)})"
                    for h in group[:8]
                ]
                evidence_blob = "\n".join(evidence_lines)
                finding_id = f"cor-{uuid.uuid4().hex[:12]}"
                conn.execute(
                    """
                    INSERT INTO security_findings
                      (scope_token, asset, location, category, title, evidence,
                       precondition, reproduction, impact, confidence, severity,
                       remediation, regression_test, status, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'open', ?, ?)
                    """,
                    (
                        scope_token,
                        asset or "unknown",
                        location or "",
                        category or "uncategorized",
                        f"Correlated: {category or 'issue'} on {asset or 'asset'}",
                        evidence_blob,
                        "; ".join(str(h.get("precondition", "")) for h in group[:4] if h.get("precondition")),
                        "; ".join(str(h.get("reproduction", "")) for h in group[:4] if h.get("reproduction")),
                        "; ".join(str(h.get("impact", "")) for h in group[:4] if h.get("impact")),
                        combined_confidence,
                        max_severity,
                        next((str(h.get("remediation", "")) for h in group if h.get("remediation")), ""),
                        next((str(h.get("regression_test", "")) for h in group if h.get("regression_test")), ""),
                        now, now,
                    ),
                )
                findings.append({
                    "finding_id": finding_id,
                    "asset": asset,
                    "location": location,
                    "category": category,
                    "severity": max_severity,
                    "confidence": combined_confidence,
                    "confidence_tier": tier,
                    "scanners": scanners,
                    "hit_count": len(group),
                    "persisted": True,
                })
    else:
        for (asset, location, category), group in groups.items():
            severities = [str(h.get("severity", "medium")).lower() for h in group]
            max_severity = max(severities, key=lambda s: severity_order.get(s, 1)) if severities else "medium"
            confidences = [float(h.get("confidence", 0.5) or 0.0) for h in group]
            avg_conf = sum(confidences) / max(len(confidences), 1)
            scanners = sorted({str(h.get("scanner", "unknown")) for h in group})
            agreement = len(scanners) / max(len(group), 1)
            tier = _confidence_tier(len(scanners), agreement, max_severity)
            combined_confidence = round(min(avg_conf + (0.1 * (len(scanners) - 1)), 1.0), 4)
            findings.append({
                "asset": asset,
                "location": location,
                "category": category,
                "severity": max_severity,
                "confidence": combined_confidence,
                "confidence_tier": tier,
                "scanners": scanners,
                "hit_count": len(group),
                "persisted": False,
            })

    findings.sort(key=lambda item: severity_order.get(item["severity"], unknown_severity_rank), reverse=True)
    return json.dumps({
        "finding_count": len(findings),
        "findings": findings,
        "persist_failures": persist_failures,
        "skipped_invalid_hits": skipped_invalid,
        "owner": sender_id,
    }, ensure_ascii=False)
