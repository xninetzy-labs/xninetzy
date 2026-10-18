from __future__ import annotations

import hashlib
import json
import logging
import time
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
from xninetzy.os.security import findings_store


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
_LIGHT_ENGINE_CONFIDENCE = 0.3
_PROTECTED_HOST_SUFFIXES = (".ac.id", ".go.id", ".mil.id")
_LAB_LOOPBACK_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})
_LAB_MAX_TTL_HOURS = 8
_LAB_DEFAULT_BUDGET = 50_000
_LAB_MAX_BUDGET = 5_000_000
_LAB_DEFAULT_RATE = 20.0
_LAB_MAX_RATE = 100.0
_LAB_PROFILES = frozenset({"passive", "active"})
_LOGGER = logging.getLogger(__name__)
_PRIVATE_ENV_WARNED = False


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
    global _PRIVATE_ENV_WARNED
    import os

    enabled = os.environ.get("XNINETZY_ALLOW_PRIVATE_TARGETS", "").strip().lower() in {
        "1", "true", "yes", "on",
    }
    if enabled and not _PRIVATE_ENV_WARNED:
        _PRIVATE_ENV_WARNED = True
        _LOGGER.warning(
            "XNINETZY_ALLOW_PRIVATE_TARGETS deprecated: gunakan security_scope(kind='owner_lab')"
        )
    return enabled


def _canonical_http(scheme: str, host: str, port: int) -> str:
    shown = f"[{host}]" if ":" in host else host
    return f"{scheme}://{shown}:{port}"


def _lab_hosts(record: dict[str, Any] | None) -> frozenset[str]:
    if not record or record.get("kind") != "owner_lab":
        return frozenset()
    return frozenset(json.loads(record.get("targets_json") or "[]"))


def _normalize_target(
    target: str, lab_hosts: frozenset[str] = frozenset()
) -> tuple[str, str, int]:
    parsed = urlparse(target.strip())
    if parsed.scheme.lower() in ("http", "https"):
        if not parsed.hostname:
            raise ValueError(f"target tidak valid: {target}")
        host = parsed.hostname.lower()
        if host.endswith(_PROTECTED_HOST_SUFFIXES):
            raise ValueError(f"target dilindungi (institusi pihak ketiga): {host}")
        port = parsed.port or (443 if parsed.scheme.lower() == "https" else 80)
        canonical = _canonical_http(parsed.scheme.lower(), host, port)
        if canonical in lab_hosts and host in _LAB_LOOPBACK_HOSTS:
            return canonical, host, port
        if not _private_ip_block_disabled() and _host_is_private(host):
            raise ValueError(f"target tidak diizinkan (host private): {host}")
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
    kind: str = "standard",
    attestation: str = "",
    profile: str = "passive",
    active_attestation: str = "",
    request_budget: int = _LAB_DEFAULT_BUDGET,
    rate_per_second: float = _LAB_DEFAULT_RATE,
    docker_network: str = "",
) -> str:
    """Daftarkan target ke scope token untuk audit keamanan resmi.

    Args:
        targets: Daftar host atau URL (maks 32).
        rationale: Alasan persetujuan (wajib non-kosong).
        ttl_hours: Durasi scope (1-720 jam, default 24; owner_lab maks 8).
        approved_by: Owner principal yang menyetujui.
        sender_id: Owner principal (dari context).
        idempotency_key: Kunci opsional.
        kind: "standard" atau "owner_lab" (hanya loopback milik owner).
        attestation: Pernyataan kepemilikan (wajib untuk owner_lab).
        profile: "passive" atau "active" (owner_lab).
        active_attestation: Pernyataan kedua, wajib untuk profile active.
        request_budget: Total request maksimum per scope owner_lab.
        rate_per_second: Batas request per detik owner_lab.
        docker_network: Belum didukung.
    """
    if not targets:
        return json.dumps({"error": "targets kosong"}, ensure_ascii=False)
    if not rationale.strip():
        return json.dumps({"error": "rationale wajib diisi"}, ensure_ascii=False)
    if kind not in {"standard", "owner_lab"}:
        return json.dumps({"error": "kind harus standard atau owner_lab"}, ensure_ascii=False)
    is_lab = kind == "owner_lab"
    if is_lab:
        if docker_network.strip():
            return json.dumps({"error": "docker_network belum didukung"}, ensure_ascii=False)
        if not attestation.strip():
            return json.dumps({"error": "attestation wajib untuk owner_lab"}, ensure_ascii=False)
        if profile not in _LAB_PROFILES:
            return json.dumps({"error": "profile harus passive atau active"}, ensure_ascii=False)
        if profile == "active" and not active_attestation.strip():
            return json.dumps({"error": "active_attestation wajib untuk profile active"}, ensure_ascii=False)
    bounded_ttl = max(1, min(ttl_hours, _LAB_MAX_TTL_HOURS if is_lab else 720))
    bounded_budget = max(1, min(int(request_budget), _LAB_MAX_BUDGET))
    bounded_rate = max(0.1, min(float(rate_per_second), _LAB_MAX_RATE))
    bounded_targets = targets[:32]
    targets_truncated = len(targets) > 32

    canonical_targets: list[str] = []
    for target in bounded_targets:
        try:
            if is_lab:
                parsed = urlparse(target.strip())
                lab_host = (parsed.hostname or "").lower()
                if parsed.scheme.lower() not in ("http", "https") or lab_host not in _LAB_LOOPBACK_HOSTS:
                    return json.dumps({
                        "error": "owner_lab hanya mengizinkan http(s) ke localhost/127.0.0.1/[::1]",
                        "target": target,
                    }, ensure_ascii=False)
                port = parsed.port or (443 if parsed.scheme.lower() == "https" else 80)
                canonical = _canonical_http(parsed.scheme.lower(), lab_host, port)
            else:
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
            if is_lab:
                conn.execute(
                    """
                    INSERT INTO security_scope_labs
                      (scope_token, profile, request_budget, requests_used,
                       rate_per_second, attestation_sha, created_at)
                    VALUES (?, ?, ?, 0, ?, ?, ?)
                    """,
                    (
                        scope_token,
                        profile,
                        bounded_budget,
                        bounded_rate,
                        hashlib.sha256(attestation.encode()).hexdigest(),
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
            "kind": kind,
        }
        if is_lab:
            payload.update({
                "profile": profile,
                "request_budget": bounded_budget,
                "rate_per_second": bounded_rate,
            })
        return json.dumps(payload, ensure_ascii=False)

    return _idempotent_call(
        "security_scope", idempotency_key,
        {
            "targets": canonical_targets, "rationale": rationale, "ttl_hours": bounded_ttl,
            "kind": kind, "profile": profile, "request_budget": bounded_budget,
            "rate_per_second": bounded_rate,
            "attestation_sha": hashlib.sha256(attestation.encode()).hexdigest() if is_lab else "",
        },
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


def _consume_lab_budget(scope_token: str) -> None:
    with connect() as conn:
        cursor = conn.execute(
            "UPDATE security_scope_labs SET requests_used = requests_used + 1 "
            "WHERE scope_token=? AND requests_used < request_budget",
            (scope_token,),
        )
        if cursor.rowcount == 0:
            raise httpx.HTTPError("lab scope: request budget habis")


def _assert_loopback_resolution(host: str) -> None:
    if _looks_like_ip(host):
        if not ipaddress.ip_address(host).is_loopback:
            raise httpx.HTTPError(f"lab scope: {host} bukan loopback")
        return
    try:
        infos = socket.getaddrinfo(host, None)
    except (socket.gaierror, OSError) as exc:
        raise httpx.HTTPError(f"lab scope: dns gagal: {exc}")
    for info in infos:
        if not ipaddress.ip_address(info[4][0]).is_loopback:
            raise httpx.HTTPError(f"lab scope: {host} berubah ke alamat non-loopback (rebinding)")


def _make_request_hook(scope_token: str, lab_hosts: frozenset[str]):
    if not lab_hosts:
        return _ssrf_safe_event_hook
    state = {"last": 0.0}

    def _hook(request: httpx.Request) -> None:
        parsed = urlparse(str(request.url))
        scheme = parsed.scheme.lower()
        if scheme not in ("http", "https"):
            raise httpx.HTTPError(f"lab scope: scheme tidak diizinkan: {scheme}")
        host = (parsed.hostname or "").lower()
        port = parsed.port or (443 if scheme == "https" else 80)
        if _canonical_http(scheme, host, port) not in lab_hosts:
            raise httpx.HTTPError(f"lab scope: {host}:{port} di luar target yang dipin")
        _assert_loopback_resolution(host)
        with connect() as conn:
            row = conn.execute(
                "SELECT rate_per_second FROM security_scope_labs WHERE scope_token=?",
                (scope_token,),
            ).fetchone()
        if not row:
            raise httpx.HTTPError("lab scope: metadata tidak ditemukan")
        _consume_lab_budget(scope_token)
        interval = 1.0 / float(row["rate_per_second"])
        wait = state["last"] + interval - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        state["last"] = time.monotonic()

    return _hook


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
    with connect() as conn:
        lab_row = conn.execute(
            "SELECT * FROM security_scope_labs WHERE scope_token=?", (scope_token,),
        ).fetchone()
    if lab_row:
        record["kind"] = "owner_lab"
        record["lab"] = dict(lab_row)
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
        canonical, _, _ = _normalize_target(target, _lab_hosts(record))
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
        canonical, host, _port = _normalize_target(target, _lab_hosts(record))
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
            event_hooks={"request": [_make_request_hook(scope_token, _lab_hosts(record))]},
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
        canonical, host, _port = _normalize_target(target, _lab_hosts(record))
    except ValueError as exc:
        return json.dumps({"error": str(exc)}, ensure_ascii=False)

    headers = {"User-Agent": "Xninetzy-SecurityHeaders/1.0"}
    try:
        with httpx.Client(
            timeout=_REQUEST_TIMEOUT,
            follow_redirects=True,
            headers=headers,
            event_hooks={"request": [_make_request_hook(scope_token, _lab_hosts(record))]},
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
        canonical, host, _port = _normalize_target(target, _lab_hosts(record))
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
            event_hooks={"request": [_make_request_hook(scope_token, _lab_hosts(record))]},
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


_SAST_SUFFIX_GLOBS = {
    ".py": "**/*.py",
    ".ts": "**/*.ts",
    ".tsx": "**/*.tsx",
    ".js": "**/*.js",
    ".jsx": "**/*.jsx",
    ".mjs": "**/*.mjs",
    ".go": "**/*.go",
    ".rb": "**/*.rb",
    ".php": "**/*.php",
    ".java": "**/*.java",
}
_SAST_SKIP_DIRS = frozenset({".git", "node_modules", ".venv", "venv", "dist", "build", "__pycache__", ".next"})
_SAST_SCAN_ENTRIES = 20000


def _detect_sast_globs(base: Path) -> list[str]:
    found: set[str] = set()
    seen = 0
    for path in base.rglob("*"):
        seen += 1
        if seen > _SAST_SCAN_ENTRIES:
            break
        if any(part in _SAST_SKIP_DIRS for part in path.relative_to(base).parts):
            continue
        glob = _SAST_SUFFIX_GLOBS.get(path.suffix.lower())
        if glob and path.is_file():
            found.add(glob)
    return sorted(found) or ["**/*.py"]


def _merge_sast_reports(reports: list[dict[str, Any]], limit: int) -> dict[str, Any]:
    severity_order = {"high": 0, "medium": 1, "low": 2}
    findings = [item for report in reports for item in report.get("findings", [])]
    findings.sort(key=lambda f: (severity_order.get(f.get("severity"), 99), f.get("file", ""), f.get("line", 0)))
    by_rule: dict[str, int] = {}
    for report in reports:
        for rule, count in (report.get("by_rule") or {}).items():
            by_rule[rule] = by_rule.get(rule, 0) + count
    bounded = max(1, min(limit, 200))
    return {
        "root": reports[0].get("root"),
        "rule_count": len(by_rule),
        "finding_count": len(findings[:bounded]),
        "truncated": len(findings) > bounded or any(r.get("truncated") for r in reports),
        "by_rule": dict(sorted(by_rule.items(), key=lambda kv: -kv[1])),
        "findings": findings[:bounded],
    }


def _record_sast_run(scope_token: str, repo_root: str, report: dict[str, Any], globs: list[str]) -> None:
    findings_store.record_run(
        scope_token, "sast-light", repo_root, "OK", int(report.get("finding_count", 0)),
        {"globs": globs, "confidence": _LIGHT_ENGINE_CONFIDENCE},
    )


@tool
def security_sast(
    scope_token: str,
    root: str = "self",
    glob: str = "",
    limit: int = 50,
    sender_id: str = "",
    engine: str = "light",
    include_tests: bool = False,
) -> str:
    """Jalankan SAST: engine light (regex, confidence rendah) atau semgrep (scanner gateway Docker).

    Args:
        scope_token: Token scope.
        root: Path atau alias repo (default self).
        glob: Pola file untuk engine light; kosong = deteksi bahasa dari isi repo.
        limit: Maks finding.
        sender_id: Owner principal.
        engine: "light" atau "semgrep"; semgrep melapor TOOL_MISSING bila docker atau image tidak ada.
        include_tests: Sertakan file test/fixture untuk rule kredensial.
    """
    if engine == "semgrep":
        from xninetzy.tools.ecosystem.security_scanner_tools import security_run_semgrep

        return security_run_semgrep.invoke({
            "scope_token": scope_token, "root": root, "limit": limit, "sender_id": sender_id,
        })
    if engine != "light":
        return json.dumps({
            "error": "engine tidak dikenal",
            "engine": engine,
            "allowed": ["light", "semgrep"],
            "scope_token": scope_token,
        }, ensure_ascii=False)
    ok, record, reason = _check_scope(scope_token, sender_id)
    if not ok or not record:
        return json.dumps({"error": reason, "scope_token": scope_token}, ensure_ascii=False)
    file_targets = _file_scope_targets(record)
    if not file_targets:
        return json.dumps({
            "error": "scope tidak berisi target file:; security_sast butuh file-scope",
            "scope_token": scope_token,
        }, ensure_ascii=False)
    repo_root = str(_resolve_repo_root(root).resolve())
    if not _root_in_file_scope(Path(repo_root), file_targets):
        return json.dumps({
            "error": "root di luar scope file target",
            "scope_token": scope_token,
            "repo_root": repo_root,
            "allowed": file_targets,
        }, ensure_ascii=False)
    from xninetzy.tools.ecosystem.repo_tools import repo_risk

    globs = [glob] if glob else _detect_sast_globs(Path(repo_root))
    reports = [
        json.loads(repo_risk.invoke({
            "root": root, "glob": pattern, "limit": limit,
            "sender_id": sender_id, "include_tests": include_tests,
        }))
        for pattern in globs
    ]
    report = reports[0] if len(reports) == 1 else _merge_sast_reports(reports, limit)
    _record_sast_run(scope_token, repo_root, report, globs)
    return json.dumps({
        "scope_token": scope_token,
        "tool": "sast-light",
        "engine": "light",
        "confidence": _LIGHT_ENGINE_CONFIDENCE,
        "globs": globs,
        "report": report,
    }, ensure_ascii=False)


def _file_scope_targets(record: dict[str, Any]) -> list[str]:
    targets = json.loads(record.get("targets_json") or "[]")
    file_targets = [
        t[len("file://"):] if t.startswith("file://") else t[len("file:"):]
        for t in targets if t.startswith("file:")
    ]
    return [p[1:] if p.startswith("//") else p for p in file_targets]


def _root_in_file_scope(root: Path, file_targets: list[str]) -> bool:
    resolved = root.resolve()
    for target in file_targets:
        base = Path(target).resolve()
        if resolved == base or resolved.is_relative_to(base):
            return True
    return False


def _reserve_lab_budget(scope_token: str, cost: int) -> bool:
    with connect() as conn:
        cursor = conn.execute(
            "UPDATE security_scope_labs SET requests_used = requests_used + ? "
            "WHERE scope_token=? AND requests_used + ? <= request_budget",
            (cost, scope_token, cost),
        )
        return cursor.rowcount == 1


def _resolve_repo_root(root: str) -> Path:
    from xninetzy.tools.ecosystem.repo_tools import _resolve_root
    return _resolve_root(root)


@tool
def security_dependencies(
    scope_token: str,
    root: str = "self",
    sender_id: str = "",
) -> str:
    """Inventaris dependency dari lockfile (npm/bun/pnpm/yarn/uv/poetry/cargo/pub/go/composer) dan requirements; tanpa penilaian kerentanan.

    Args:
        scope_token: Token scope.
        root: Path atau alias repo.
        sender_id: Owner principal.
    """
    ok, record, reason = _check_scope(scope_token, sender_id)
    if not ok or not record:
        return json.dumps({"error": reason, "scope_token": scope_token}, ensure_ascii=False)
    file_targets = _file_scope_targets(record)
    if not file_targets:
        return json.dumps({
            "error": "scope tidak berisi target file:; security_dependencies butuh file-scope",
            "scope_token": scope_token,
        }, ensure_ascii=False)
    base = _resolve_repo_root(root).resolve()
    repo_root = str(base)
    if not _root_in_file_scope(base, file_targets):
        return json.dumps({
            "error": "root di luar scope file target",
            "scope_token": scope_token,
            "repo_root": repo_root,
            "allowed": file_targets,
        }, ensure_ascii=False)
    from xninetzy.os.security import lockfiles

    lock_paths = lockfiles.discover(base)
    seen: set[tuple[str, str, str]] = set()
    deps: list[dict[str, Any]] = []
    lockfile_summary: list[dict[str, Any]] = []
    parse_errors: list[dict[str, str]] = []
    for path in lock_paths:
        rel = str(path.relative_to(base))
        try:
            packages = lockfiles.parse_lockfile(path, base)
        except (ValueError, OSError) as exc:
            parse_errors.append({"lockfile": rel, "error": type(exc).__name__})
            continue
        lockfile_summary.append({"lockfile": rel, "packages": len(packages)})
        for pkg in packages:
            key = (pkg.ecosystem, pkg.name, pkg.version)
            if key in seen:
                continue
            seen.add(key)
            deps.append({
                "name": pkg.name,
                "version": pkg.version,
                "version_hint": pkg.version,
                "ecosystem": pkg.ecosystem,
                "dev": pkg.dev,
                "source": rel,
            })
    pyproject = base / "pyproject.toml"
    manifest = lockfiles.manifest_dependencies(pyproject) if pyproject.exists() else []
    payload = {
        "scope_token": scope_token,
        "root": str(base),
        "dependency_count": len(deps),
        "lockfile_count": len(lockfile_summary),
        "lockfiles": lockfile_summary,
        "parse_errors": parse_errors,
        "manifest_dependencies": manifest,
        "dependencies": deps,
        "vulnerabilities": "NOT_ASSESSED",
        "vulnerability_note": "hasil ini hanya inventaris; jalankan security_run_osv atau security_run_trivy untuk advisory",
    }
    findings_store.record_run(
        scope_token, "dependency-inventory", str(base), "OK", len(deps),
        {"lockfiles": len(lockfile_summary), "parse_errors": len(parse_errors)},
    )
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
