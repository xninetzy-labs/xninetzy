from __future__ import annotations

import json
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import pytest

from xninetzy.os.security import findings_store
from xninetzy.tools.ecosystem.security_probe_tools import security_http_probe
from xninetzy.tools.ecosystem.security_tools import security_scope

SECURE_HEADERS = {
    "Content-Security-Policy": "default-src 'self'",
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "geolocation=()",
}


def _make_handler(vulnerable: bool):
    class Handler(BaseHTTPRequestHandler):
        counter = {"get": 0}

        def version_string(self):
            return "srv" if not vulnerable else "nginx/1.18.0"

        def log_message(self, *args):
            return

        def _send(self, status, body, extra=None):
            payload = body if isinstance(body, bytes) else json.dumps(body).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            origin = self.headers.get("Origin")
            if vulnerable and origin:
                self.send_header("Access-Control-Allow-Origin", origin)
                self.send_header("Access-Control-Allow-Credentials", "true")
            if not vulnerable:
                for key, value in SECURE_HEADERS.items():
                    self.send_header(key, value)
            for key, value in (extra or {}).items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(payload)

        def _execute(self, query: str, is_get: bool):
            if query.count("{") != query.count("}"):
                text = 'Error at Object.parse (/app/node_modules/graphql/parse.js:10:5)' if vulnerable else "Bad request"
                return self._send(400, {"errors": [{"message": text}]})
            if "mutation" in query and is_get:
                if vulnerable:
                    return self._send(200, {"data": {"__typename": "Mutation"}})
                return self._send(405, {"errors": [{"message": "GET mutation"}]})
            if "__schema" in query:
                if vulnerable:
                    return self._send(200, {"data": {"__schema": {"queryType": {"name": "Query"}}}})
                return self._send(400, {"errors": [{"message": "introspection disabled"}]})
            if query.count("ofType{") > 10 and not vulnerable:
                return self._send(400, {"errors": [{"message": "too deep"}]})
            aliases = len(re.findall(r"a\d+:__typename", query))
            if aliases > 100 and not vulnerable:
                return self._send(400, {"errors": [{"message": "too many aliases"}]})
            if aliases:
                return self._send(200, {"data": {f"a{i}": "Query" for i in range(aliases)}})
            return self._send(200, {"data": {"__typename": "Query"}})

        def do_GET(self):
            parsed = urlparse(self.path)
            if parsed.path == "/":
                return self._send(200, {"ok": True})
            Handler.counter["get"] += 1
            if not vulnerable and Handler.counter["get"] > 20 and self.headers.get("X-Forwarded-For"):
                return self._send(429, {"errors": [{"message": "rate limited"}]})
            return self._execute(parse_qs(parsed.query).get("query", [""])[0], True)

        def do_OPTIONS(self):
            self._send(204, b"")

        def do_TRACE(self):
            if vulnerable:
                return self._send(200, b"TRACE")
            return self._send(405, b"no")

        def do_POST(self):
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length).decode()
            ctype = self.headers.get("Content-Type", "")
            if "json" not in ctype and not vulnerable:
                return self._send(415, {"errors": [{"message": "unsupported"}]})
            if "x-www-form-urlencoded" in ctype:
                return self._execute(parse_qs(raw).get("query", [""])[0], False)
            try:
                body = json.loads(raw)
            except ValueError:
                return self._execute("{ __typename ", False)
            if isinstance(body, list):
                if not vulnerable:
                    return self._send(400, {"errors": [{"message": "batching disabled"}]})
                return self._send(200, [{"data": {"__typename": "Query"}} for _ in body])
            return self._execute(body.get("query", ""), False)

    return Handler


def _serve(vulnerable: bool):
    server = ThreadingHTTPServer(("127.0.0.1", 0), _make_handler(vulnerable))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


@pytest.fixture(scope="module")
def vulnerable_server():
    server, url = _serve(True)
    yield url
    server.shutdown()


@pytest.fixture(scope="module")
def hardened_server():
    server, url = _serve(False)
    yield url
    server.shutdown()


@pytest.fixture(autouse=True)
def env(tmp_path, monkeypatch):
    monkeypatch.delenv("XNINETZY_ALLOW_PRIVATE_TARGETS", raising=False)
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "t.sqlite3"))
    from xninetzy.core.config import get_settings

    get_settings.cache_clear()
    yield


def _lab(url, **extra):
    params = {"targets": [url], "rationale": "lab", "kind": "owner_lab", "attestation": "saya pemilik", "rate_per_second": 100}
    params.update(extra)
    return json.loads(security_scope.invoke(params))["scope_token"]


def _probe(scope, url, **kw):
    return json.loads(security_http_probe.invoke({"scope_token": scope, "base_url": url, **kw}))


def _by_id(out):
    return {c["id"]: c for c in out["checks"]}


def test_vulnerable_target_reports_cors_csrf_introspection_and_more(vulnerable_server):
    out = _probe(_lab(vulnerable_server), vulnerable_server, production=True)
    checks = _by_id(out)
    for check_id in ("cors_reflection", "csrf_content_types", "graphql_introspection", "graphql_get_mutation",
                     "graphql_batching_aliases", "graphql_depth", "error_masking", "trace_method"):
        assert checks[check_id]["status"] == "fail", check_id
    assert checks["origin_enforcement"]["status"] == "warn"
    assert checks["security_headers"]["status"] == "warn"
    assert "node_modules" in checks["error_masking"]["evidence"] or "stack" in checks["error_masking"]["evidence"]
    assert out["summary"]["fail"] == 8


def test_hardened_target_reports_no_failures(hardened_server):
    out = _probe(_lab(hardened_server), hardened_server, production=True)
    assert out["summary"]["fail"] == 0, out["checks"]
    checks = _by_id(out)
    assert checks["cors_reflection"]["status"] == "pass"
    assert checks["csrf_content_types"]["status"] == "pass"
    assert checks["graphql_introspection"]["status"] == "pass"
    assert checks["security_headers"]["status"] == "pass"
    assert checks["rate_limit_spoofing"]["status"] == "skip"


def test_introspection_is_only_a_warning_outside_production(vulnerable_server):
    out = _probe(_lab(vulnerable_server), vulnerable_server, production=False)
    assert _by_id(out)["graphql_introspection"]["status"] == "warn"


def test_rate_limit_check_needs_active_profile_and_budget(hardened_server, vulnerable_server):
    passive = _lab(hardened_server)
    assert "active" in _probe(passive, hardened_server, profile="active", budget=30)["error"]
    active = _lab(hardened_server, profile="active", active_attestation="izin aktif")
    out = _probe(active, hardened_server, profile="active", budget=40)
    assert _by_id(out)["rate_limit_spoofing"]["status"] == "pass"
    no_budget = _probe(active, hardened_server, profile="active")
    assert _by_id(no_budget)["rate_limit_spoofing"]["status"] == "skip"
    vuln_scope = _lab(vulnerable_server, profile="active", active_attestation="izin aktif")
    bad = _probe(vuln_scope, vulnerable_server, profile="active", budget=30)
    assert _by_id(bad)["rate_limit_spoofing"]["status"] == "fail"


def test_probe_respects_lab_budget_and_reports_errors(hardened_server):
    scope = _lab(hardened_server, request_budget=5)
    out = _probe(scope, hardened_server)
    assert out["summary"]["error"] >= 1
    assert any("budget" in c["evidence"] for c in out["checks"] if c["status"] == "error")


def test_probe_refuses_bad_input(hardened_server, vulnerable_server):
    scope = _lab(hardened_server)
    assert "scope" in _probe(scope, vulnerable_server)["error"]
    assert "error" in _probe(scope, hardened_server, profile="nuclear")
    assert "error" in _probe(scope, hardened_server, graphql_path="graphql")
    assert "error" in _probe("sec-nope", hardened_server)
    standard = json.loads(security_scope.invoke({"targets": ["http://localhost:1"], "rationale": "x"}))
    assert "private" in standard["error"]


def test_findings_are_persisted_once_and_runs_recorded(vulnerable_server):
    scope = _lab(vulnerable_server)
    first = _probe(scope, vulnerable_server, production=True, persist=True)
    assert first["persisted"]["created"] == 8
    second = _probe(scope, vulnerable_server, production=True, persist=True)
    assert second["persisted"] == {"created": 0, "seen": 8, "reopened": 0}
    rows = findings_store.list_findings(scope)
    assert len(rows) == 8 and all(r["reproduction"] == "runtime-proof" for r in rows)
    runs = findings_store.list_runs(scope)
    assert sum(1 for r in runs if r["tool"] == "http_probe") == 2 * len(first["checks"])
