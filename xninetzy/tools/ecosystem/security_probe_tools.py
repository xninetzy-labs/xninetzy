from __future__ import annotations

import json
import re
from collections import Counter
from typing import Any

import httpx
from langchain_core.tools import tool

from xninetzy.db.sqlite import connect, init_db
from xninetzy.os.security import findings_store
from xninetzy.os.security.guards import redact_secrets
from xninetzy.tools.ecosystem.security_tools import (
    _REQUEST_TIMEOUT,
    _SECURITY_HEADERS,
    _check_scope,
    _lab_hosts,
    _make_request_hook,
    _matches_scope,
    _normalize_target,
)

FOREIGN_ORIGIN = "https://evil.example"
ALIAS_COUNT = 200
DEPTH_LEVELS = 20
RATE_LIMIT_MAX_REQUESTS = 500
_STACK_TRACE = re.compile(
    r"(\bat\s+\S+\s+\([^)]*:\d+:\d+\))|Traceback \(most recent call last\)|node_modules[/\\]|\.(?:ts|js|py|java):\d+|\"stack\"\s*:",
    re.IGNORECASE,
)
_SERVER_VERSION = re.compile(r"\d+\.\d+")
_SEVERITY = {
    "cors_reflection": "medium",
    "csrf_content_types": "medium",
    "origin_enforcement": "low",
    "graphql_introspection": "low",
    "graphql_get_mutation": "medium",
    "graphql_batching_aliases": "low",
    "graphql_depth": "low",
    "error_masking": "low",
    "trace_method": "low",
    "security_headers": "info",
    "rate_limit_spoofing": "medium",
}


def _result(check: str, status: str, evidence: str) -> dict[str, str]:
    return {"id": check, "status": status, "severity": _SEVERITY.get(check, "info"), "evidence": redact_secrets(evidence)[:300]}


def _json_body(response: httpx.Response) -> Any:
    try:
        return response.json()
    except ValueError:
        return None


def _executes_query(response: httpx.Response) -> bool:
    if not 200 <= response.status_code < 300:
        return False
    body = _json_body(response)
    if isinstance(body, list):
        return any(isinstance(item, dict) and item.get("data") for item in body)
    return isinstance(body, dict) and bool(body.get("data"))


class _Prober:
    def __init__(self, client: httpx.Client, base: str, graphql: str) -> None:
        self.client = client
        self.base = base
        self.graphql = f"{base}{graphql}"
        self.requests_sent = 0

    def send(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        self.requests_sent += 1
        return self.client.request(method, url, **kwargs)

    def post_gql(self, body: Any, headers: dict[str, str] | None = None, content: str | None = None) -> httpx.Response:
        merged = {"Content-Type": "application/json", **(headers or {})}
        if content is not None:
            return self.send("POST", self.graphql, content=content, headers=merged)
        return self.send("POST", self.graphql, json=body, headers=merged)


def _check_cors(p: _Prober) -> dict[str, str]:
    problems: list[str] = []
    for origin in (FOREIGN_ORIGIN, "null"):
        for method in ("GET", "OPTIONS"):
            headers = {"Origin": origin}
            if method == "OPTIONS":
                headers["Access-Control-Request-Method"] = "POST"
            response = p.send(method, p.graphql, headers=headers, params={"query": "{__typename}"} if method == "GET" else None)
            allow = response.headers.get("access-control-allow-origin", "")
            credentials = response.headers.get("access-control-allow-credentials", "").lower() == "true"
            if credentials and allow == origin:
                problems.append(f"{method} Origin:{origin} reflected with credentials")
            elif credentials and allow == "*":
                problems.append(f"{method} wildcard origin with credentials")
    if problems:
        return _result("cors_reflection", "fail", "; ".join(problems))
    return _result("cors_reflection", "pass", "no origin reflected with credentials")


def _check_csrf(p: _Prober) -> dict[str, str]:
    accepted: list[str] = []
    form = p.send("POST", p.graphql, content="query=%7B__typename%7D", headers={"Content-Type": "application/x-www-form-urlencoded"})
    if _executes_query(form):
        accepted.append("application/x-www-form-urlencoded")
    text = p.send("POST", p.graphql, content='{"query":"{__typename}"}', headers={"Content-Type": "text/plain"})
    if _executes_query(text):
        accepted.append("text/plain")
    if accepted:
        return _result("csrf_content_types", "fail", f"operations executed for non-JSON content types: {', '.join(accepted)}")
    return _result("csrf_content_types", "pass", "non-JSON content types rejected")


def _check_origin(p: _Prober) -> dict[str, str]:
    response = p.post_gql({"query": "{__typename}"}, {"Origin": FOREIGN_ORIGIN})
    if _executes_query(response):
        return _result("origin_enforcement", "warn", f"foreign Origin accepted with {response.status_code}; verify the endpoint is state-changing")
    return _result("origin_enforcement", "pass", f"foreign Origin rejected with {response.status_code}")


def _check_introspection(p: _Prober, production: bool) -> dict[str, str]:
    response = p.post_gql({"query": "{ __schema { queryType { name } } }"})
    body = _json_body(response)
    open_ = _executes_query(response) and isinstance(body, dict) and "__schema" in (body.get("data") or {})
    if open_:
        return _result("graphql_introspection", "fail" if production else "warn", "anonymous introspection succeeded")
    return _result("graphql_introspection", "pass", f"introspection refused with {response.status_code}")


def _check_get_mutation(p: _Prober) -> dict[str, str]:
    response = p.send("GET", p.graphql, params={"query": "mutation{__typename}"})
    if response.status_code == 405:
        return _result("graphql_get_mutation", "pass", "405 for mutation over GET")
    if _executes_query(response):
        return _result("graphql_get_mutation", "fail", f"mutation executed over GET ({response.status_code})")
    return _result("graphql_get_mutation", "warn", f"expected 405, got {response.status_code}")


def _check_batching(p: _Prober) -> dict[str, str]:
    problems: list[str] = []
    batch = p.post_gql([{"query": "{__typename}"}, {"query": "{__typename}"}])
    if _executes_query(batch) and isinstance(_json_body(batch), list):
        problems.append("array batching executed")
    aliases = " ".join(f"a{i}:__typename" for i in range(ALIAS_COUNT))
    alias_response = p.post_gql({"query": f"{{{aliases}}}"})
    body = _json_body(alias_response)
    if _executes_query(alias_response) and isinstance(body, dict) and len(body.get("data") or {}) >= ALIAS_COUNT:
        problems.append(f"{ALIAS_COUNT} aliases executed")
    if problems:
        return _result("graphql_batching_aliases", "fail", "; ".join(problems))
    return _result("graphql_batching_aliases", "pass", "batching and alias floods limited")


def _check_depth(p: _Prober) -> dict[str, str]:
    nested = "ofType{" * DEPTH_LEVELS + "name" + "}" * DEPTH_LEVELS
    response = p.post_gql({"query": f'{{ __type(name: "Query") {{ {nested} }} }}'})
    body = _json_body(response)
    if 200 <= response.status_code < 300 and isinstance(body, dict) and not body.get("errors"):
        return _result("graphql_depth", "fail", f"{DEPTH_LEVELS}-level query accepted")
    return _result("graphql_depth", "pass", f"deep query rejected with {response.status_code}")


def _check_error_masking(p: _Prober) -> dict[str, str]:
    response = p.post_gql(None, content='{"query":"{ __typename "}')
    if _STACK_TRACE.search(response.text[:20000]):
        return _result("error_masking", "fail", "stack trace or source path in error response")
    return _result("error_masking", "pass", f"errors masked ({response.status_code})")


def _check_trace(p: _Prober) -> dict[str, str]:
    response = p.send("TRACE", p.base + "/")
    if 200 <= response.status_code < 300:
        return _result("trace_method", "fail", f"TRACE allowed ({response.status_code})")
    return _result("trace_method", "pass", f"TRACE refused ({response.status_code})")


def _check_headers(p: _Prober) -> dict[str, str]:
    response = p.send("GET", p.base + "/")
    present = {name.lower() for name in response.headers}
    https = p.base.startswith("https://")
    expected = [h for h in _SECURITY_HEADERS if h != "x-xss-protection" and (https or h != "strict-transport-security")]
    missing = [h for h in expected if h not in present]
    server = response.headers.get("server", "")
    notes: list[str] = []
    if missing:
        notes.append("missing: " + ", ".join(missing))
    if _SERVER_VERSION.search(server):
        notes.append(f"Server discloses version: {server}")
    if notes:
        return _result("security_headers", "warn", "; ".join(notes))
    return _result("security_headers", "pass", "security headers present")


def _check_rate_limit(p: _Prober, budget: int) -> dict[str, str]:
    total = max(1, min(budget, RATE_LIMIT_MAX_REQUESTS))
    limited = 0
    for i in range(total):
        headers = {"X-Forwarded-For": f"10.{(i // 65025) % 250}.{(i // 255) % 255}.{i % 255 + 1}"}
        if p.send("GET", p.graphql, params={"query": "{__typename}"}, headers=headers).status_code == 429:
            limited += 1
    if limited == 0:
        return _result("rate_limit_spoofing", "fail", f"no 429 in {total} requests with rotating X-Forwarded-For")
    return _result("rate_limit_spoofing", "pass", f"{limited} of {total} requests limited")


def _persist_failures(scope_token: str, base_url: str, graphql_path: str, checks: list[dict[str, str]]) -> dict[str, int]:
    init_db()
    outcome: Counter[str] = Counter()
    with connect() as conn:
        for check in checks:
            if check["status"] != "fail":
                continue
            fingerprint = findings_store.location_fingerprint(base_url, graphql_path, check["id"])
            _fid, result = findings_store.upsert_finding(
                conn, scope_token,
                fingerprint=fingerprint, asset=base_url, location=graphql_path, category=check["id"],
                title=f"http_probe: {check['id']}", evidence=check["evidence"], severity=check["severity"],
                confidence=0.8, reproduction="runtime-proof",
            )
            outcome[result] += 1
    return {key: outcome.get(key, 0) for key in ("created", "seen", "reopened")}


@tool(description="Probe HTTP/GraphQL terbatas dan read-only pada target dalam scope: CORS, CSRF content type, origin, introspeksi, GET mutation, batching/alias, depth, error masking, TRACE, header, rate-limit spoofing (profile active + budget).")
def security_http_probe(
    scope_token: str,
    base_url: str,
    profile: str = "passive",
    graphql_path: str = "/graphql",
    production: bool = False,
    budget: int = 0,
    persist: bool = False,
    sender_id: str = "",
) -> str:
    ok, record, reason = _check_scope(scope_token, sender_id)
    if not ok or not record:
        return json.dumps({"error": reason, "scope_token": scope_token}, ensure_ascii=False)
    if profile not in {"passive", "active"}:
        return json.dumps({"error": "profile harus passive atau active"}, ensure_ascii=False)
    lab = record.get("lab") or {}
    if profile == "active" and lab.get("profile") != "active":
        return json.dumps({"error": "profile active butuh scope owner_lab dengan profile active"}, ensure_ascii=False)
    if not _matches_scope(record, base_url):
        return json.dumps({"error": "target tidak termasuk scope"}, ensure_ascii=False)
    if not graphql_path.startswith("/"):
        return json.dumps({"error": "graphql_path harus diawali /"}, ensure_ascii=False)
    try:
        canonical, _host, _port = _normalize_target(base_url, _lab_hosts(record))
    except ValueError as exc:
        return json.dumps({"error": str(exc)}, ensure_ascii=False)
    checks: list[dict[str, str]] = []
    prober: _Prober | None = None
    plan = [
        lambda p: _check_cors(p),
        lambda p: _check_csrf(p),
        lambda p: _check_origin(p),
        lambda p: _check_introspection(p, production),
        lambda p: _check_get_mutation(p),
        lambda p: _check_batching(p),
        lambda p: _check_depth(p),
        lambda p: _check_error_masking(p),
        lambda p: _check_trace(p),
        lambda p: _check_headers(p),
    ]
    ids = ["cors_reflection", "csrf_content_types", "origin_enforcement", "graphql_introspection", "graphql_get_mutation",
           "graphql_batching_aliases", "graphql_depth", "error_masking", "trace_method", "security_headers"]
    if profile == "active" and budget > 0:
        plan.append(lambda p: _check_rate_limit(p, budget))
        ids.append("rate_limit_spoofing")
    with httpx.Client(
        timeout=_REQUEST_TIMEOUT,
        follow_redirects=False,
        headers={"User-Agent": "Xninetzy-HttpProbe/1.0"},
        event_hooks={"request": [_make_request_hook(scope_token, _lab_hosts(record))]},
    ) as client:
        prober = _Prober(client, canonical, graphql_path)
        for check_id, fn in zip(ids, plan):
            try:
                checks.append(fn(prober))
            except httpx.HTTPError as exc:
                checks.append(_result(check_id, "error", f"{type(exc).__name__}: {exc}"))
    if profile == "active" and budget <= 0:
        checks.append(_result("rate_limit_spoofing", "skip", "butuh budget eksplisit"))
    elif profile == "passive":
        checks.append(_result("rate_limit_spoofing", "skip", "hanya profile active"))
    for check in checks:
        findings_store.record_run(
            scope_token, "http_probe", f"{canonical}#{check['id']}", check["status"],
            1 if check["status"] == "fail" else 0, {"evidence": check["evidence"]},
        )
    summary = Counter(c["status"] for c in checks)
    payload: dict[str, Any] = {
        "scope_token": scope_token,
        "base_url": canonical,
        "profile": profile,
        "requests_sent": prober.requests_sent if prober else 0,
        "summary": {name: summary.get(name, 0) for name in ("pass", "fail", "warn", "skip", "error")},
        "checks": checks,
    }
    if persist:
        payload["persisted"] = _persist_failures(scope_token, canonical, graphql_path, checks)
    return json.dumps(payload, ensure_ascii=False)

