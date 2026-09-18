from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from xninetzy.tools.ecosystem.security_tools import (
    security_api_inventory,
    security_assets,
    security_dependencies,
    security_headers,
    security_regression,
    security_sast,
    security_scope,
    security_threat_model,
    security_validate_finding,
)


SECURE_HEADERS_HTML = b"""
<html><head>
  <meta http-equiv="Strict-Transport-Security" content="max-age=31536000">
  <meta http-equiv="X-Frame-Options" content="DENY">
</head><body>ok</body></html>
"""

COOKIE_BANNER = b"Set-Cookie: sessionid=abc123; Path=/\r\n"


class _SecurityHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Strict-Transport-Security", "max-age=31536000")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Content-Security-Policy", "default-src 'self'")
            self.send_header("Content-Length", str(len(SECURE_HEADERS_HTML)))
            self.end_headers()
            self.wfile.write(SECURE_HEADERS_HTML)
        elif self.path == "/.well-known/openapi.json":
            body = b'{"openapi":"3.0.0","paths":{}}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()


@pytest.fixture(scope="module")
def mock_server():
    server = ThreadingHTTPServer(("127.0.0.1", 0), _SecurityHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        thread.join(timeout=2)


@pytest.fixture
def sqlite_env(tmp_path, monkeypatch):
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "test.sqlite3"))
    from xninetzy.core.config import get_settings
    get_settings.cache_clear()
    yield tmp_path


def _invoke(tool, **kwargs) -> dict:
    return json.loads(tool.invoke(kwargs))


def test_security_scope_rejects_empty_rationale(sqlite_env):
    out = _invoke(security_scope, targets=["https://example.com"], rationale="")
    assert "error" in out


def test_security_scope_rejects_invalid_url(sqlite_env):
    out = _invoke(security_scope, targets=["not-a-url"], rationale="audit")
    assert "error" in out


def test_security_scope_creates_token(sqlite_env):
    out = _invoke(
        security_scope,
        targets=["https://example.com", "http://other.example.com:80"],
        rationale="audit",
        ttl_hours=12,
    )
    assert "scope_token" in out
    assert out["target_count"] == 2
    assert "expires_at" in out


def test_security_assets_denied_without_scope(sqlite_env):
    out = _invoke(
        security_assets,
        scope_token="sec-missing",
        target="https://example.com",
    )
    assert "error" in out


def test_security_assets_denied_for_out_of_scope_target(sqlite_env):
    scope = _invoke(
        security_scope,
        targets=["https://example.com"],
        rationale="audit",
    )
    out = _invoke(
        security_assets,
        scope_token=scope["scope_token"],
        target="https://attacker.example.com",
    )
    assert "error" in out


def test_security_assets_enumerates_seed_paths(sqlite_env, mock_server):
    scope = _invoke(
        security_scope,
        targets=[mock_server],
        rationale="audit",
    )
    out = _invoke(
        security_assets,
        scope_token=scope["scope_token"],
        target=mock_server,
        limit=10,
    )
    assert "assets" in out
    assert out["asset_count"] >= 1


def test_security_headers_reports_missing(sqlite_env, mock_server):
    scope = _invoke(security_scope, targets=[mock_server], rationale="audit")
    out = _invoke(
        security_headers,
        scope_token=scope["scope_token"],
        target=mock_server,
    )
    assert "present" in out
    assert "missing" in out
    assert out["header_score"] >= 0


def test_security_api_inventory_finds_spec(sqlite_env, mock_server):
    scope = _invoke(security_scope, targets=[mock_server], rationale="audit")
    out = _invoke(
        security_api_inventory,
        scope_token=scope["scope_token"],
        target=mock_server,
    )
    assert "found" in out
    assert any(item.get("kind") == "spec" for item in out["found"])


def test_security_sast_runs_repo_risk(sqlite_env):
    scope = _invoke(security_scope, targets=["http://127.0.0.1:1"], rationale="audit")
    out = _invoke(
        security_sast,
        scope_token=scope["scope_token"],
        root="self",
        limit=5,
    )
    assert out["tool"] == "sast-light"
    assert "report" in out


def test_security_dependencies_returns_inventory(sqlite_env):
    scope = _invoke(security_scope, targets=["http://127.0.0.1:1"], rationale="audit")
    out = _invoke(
        security_dependencies,
        scope_token=scope["scope_token"],
        root="self",
    )
    assert "dependencies" in out
    assert isinstance(out["dependencies"], list)


def test_security_threat_model_scores_signals(sqlite_env):
    scope = _invoke(security_scope, targets=["http://127.0.0.1:1"], rationale="audit")
    out = _invoke(
        security_threat_model,
        scope_token=scope["scope_token"],
        inventory_summary="login endpoint dengan jwt token dan sql query",
    )
    assert "edges" in out
    classes = {edge["threat_class"] for edge in out["edges"]}
    assert "authn_z" in classes


def test_security_validate_finding_persists(sqlite_env):
    scope = _invoke(security_scope, targets=["http://127.0.0.1:1"], rationale="audit")
    out = _invoke(
        security_validate_finding,
        scope_token=scope["scope_token"],
        title="SQL format string",
        asset="db/query.py",
        location="db/query.py:42",
        category="sql_injection",
        evidence="execute(f\"SELECT * FROM users WHERE id={uid}\")",
        severity="high",
        confidence=0.9,
        allow_runtime_proof=False,
    )
    assert out["id"] >= 1
    assert out["reproduction"] == "static-evidence"


def test_security_validate_finding_records_runtime_proof_flag(sqlite_env):
    scope = _invoke(security_scope, targets=["http://127.0.0.1:1"], rationale="audit")
    out = _invoke(
        security_validate_finding,
        scope_token=scope["scope_token"],
        title="Lab XSS",
        asset="lab/app.py",
        location="lab/app.py:1",
        category="xss",
        evidence="lab run",
        allow_runtime_proof=True,
    )
    assert out["reproduction"] == "runtime-proof"


def test_security_regression_links_test(sqlite_env):
    scope = _invoke(security_scope, targets=["http://127.0.0.1:1"], rationale="audit")
    finding = _invoke(
        security_validate_finding,
        scope_token=scope["scope_token"],
        title="Title",
        asset="a.py",
        location="a.py:1",
        category="x",
        evidence="e",
    )
    out = _invoke(
        security_regression,
        scope_token=scope["scope_token"],
        finding_id=finding["id"],
        test_id="tests/test_x.py",
        status="proposed",
    )
    assert out["status"] == "proposed"
    assert out["test_id"] == "tests/test_x.py"


def test_security_regression_rejects_finding_outside_scope(sqlite_env):
    scope = _invoke(security_scope, targets=["http://127.0.0.1:1"], rationale="audit")
    out = _invoke(
        security_regression,
        scope_token=scope["scope_token"],
        finding_id=999999,
    )
    assert "error" in out
