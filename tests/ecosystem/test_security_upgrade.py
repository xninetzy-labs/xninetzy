from __future__ import annotations

import json
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from xninetzy.db.sqlite import connect
from xninetzy.os.security import lockfiles
from xninetzy.skills.tools import skill_resource_read
from xninetzy.tools.ecosystem import security_tools
from xninetzy.tools.ecosystem.repo_tools import repo_risk
from xninetzy.tools.ecosystem.security_tools import (
    security_assets,
    security_dependencies,
    security_headers,
    security_sast,
    security_scope,
)


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def do_GET(self):
        if self.path == "/redir":
            self.send_response(302)
            self.send_header("Location", "http://127.0.0.1:1/elsewhere")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        body = b"ok"
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


@pytest.fixture(scope="module")
def lab_server():
    server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        thread.join(timeout=2)


@pytest.fixture(autouse=True)
def strict_private_block(tmp_path, monkeypatch):
    monkeypatch.delenv("XNINETZY_ALLOW_PRIVATE_TARGETS", raising=False)
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "test.sqlite3"))
    from xninetzy.core.config import get_settings

    get_settings.cache_clear()
    yield


def _invoke(tool, **kwargs) -> dict:
    return json.loads(tool.invoke(kwargs))


def _lab(targets, **extra) -> dict:
    params = {
        "targets": targets,
        "rationale": "lab pribadi",
        "kind": "owner_lab",
        "attestation": "saya pemilik stack ini",
    }
    params.update(extra)
    return _invoke(security_scope, **params)


def _used(scope_token: str) -> int:
    with connect() as conn:
        row = conn.execute(
            "SELECT requests_used FROM security_scope_labs WHERE scope_token=?", (scope_token,)
        ).fetchone()
    return row["requests_used"]


def test_localhost_rejected_for_standard_scope():
    out = _invoke(security_scope, targets=["http://localhost:8080"], rationale="x")
    assert "private" in out["error"]


@pytest.mark.parametrize("host", ["fst.unair.ac.id", "data.go.id", "x.mil.id"])
def test_protected_suffixes_refused_even_with_private_override(host, monkeypatch):
    out = _invoke(security_scope, targets=[f"https://{host}"], rationale="x")
    assert "dilindungi" in out["error"]
    monkeypatch.setenv("XNINETZY_ALLOW_PRIVATE_TARGETS", "true")
    assert "dilindungi" in _invoke(security_scope, targets=[f"https://{host}"], rationale="x")["error"]
    assert "error" in _lab([f"https://{host}"])


def test_look_alike_hosts_are_not_treated_as_protected():
    out = _invoke(security_scope, targets=["https://notac.id.example.com"], rationale="x")
    assert "error" not in out


def test_owner_lab_allows_loopback_and_pins_canonical_form(lab_server):
    out = _lab([lab_server, "http://[::1]:9000"])
    assert out["kind"] == "owner_lab"
    assert out["targets"][0].startswith("http://127.0.0.1:")
    assert "http://[::1]:9000" in out["targets"]


def test_owner_lab_rejects_public_and_protected_hosts():
    assert "loopback" in _lab(["https://example.com"])["error"] or "localhost" in _lab(["https://example.com"])["error"]
    assert "error" in _lab(["https://fst.unair.ac.id"])
    assert "error" in _lab(["http://192.168.1.10:8080"])


def test_owner_lab_requires_attestation_and_second_attestation_for_active():
    assert "attestation" in _lab(["http://localhost:1"], attestation="")["error"]
    assert "active_attestation" in _lab(["http://localhost:1"], profile="active")["error"]
    ok = _lab(["http://localhost:1"], profile="active", active_attestation="izin aktif")
    assert ok["profile"] == "active"


def test_owner_lab_caps_ttl_and_rejects_docker_network():
    assert _lab(["http://localhost:1"], ttl_hours=500)["ttl_hours"] == 8
    assert "docker_network" in _lab(["http://localhost:1"], docker_network="x")["error"]


def test_owner_lab_scope_drives_headers_tool(lab_server):
    scope = _lab([lab_server])
    out = _invoke(security_headers, scope_token=scope["scope_token"], target=lab_server)
    assert "error" not in out
    assert _used(scope["scope_token"]) >= 1


def test_owner_lab_budget_is_enforced(lab_server):
    scope = _lab([lab_server], request_budget=1)
    out = _invoke(security_assets, scope_token=scope["scope_token"], target=lab_server)
    errors = [a.get("error", "") for a in out.get("assets", [])]
    assert any("budget" in e for e in errors)
    assert _used(scope["scope_token"]) == 1


def test_owner_lab_rejects_rebinding_to_non_loopback(monkeypatch):
    scope = _lab(["http://localhost:8080"])
    real = socket.getaddrinfo

    def fake(host, *args, **kwargs):
        if host == "localhost":
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))]
        return real(host, *args, **kwargs)

    monkeypatch.setattr(security_tools.socket, "getaddrinfo", fake)
    out = _invoke(security_assets, scope_token=scope["scope_token"], target="http://localhost:8080")
    assert any("rebinding" in a.get("error", "") for a in out["assets"])


def test_owner_lab_redirect_outside_pinned_targets_is_blocked(lab_server):
    scope = _lab([lab_server])
    hook = security_tools._make_request_hook(
        scope["scope_token"], security_tools._lab_hosts({"kind": "owner_lab", "targets_json": json.dumps(scope["targets"])})
    )
    import httpx

    with pytest.raises(httpx.HTTPError, match="di luar target"):
        hook(httpx.Request("GET", "http://127.0.0.1:1/elsewhere"))
    with pytest.raises(httpx.HTTPError, match="di luar target"):
        hook(httpx.Request("GET", "https://example.com/"))


def test_owner_lab_target_not_in_scope_is_refused(lab_server):
    scope = _lab([lab_server])
    out = _invoke(security_headers, scope_token=scope["scope_token"], target="http://127.0.0.1:1")
    assert "error" in out


def test_env_switch_logs_deprecation(monkeypatch, caplog):
    monkeypatch.setenv("XNINETZY_ALLOW_PRIVATE_TARGETS", "true")
    monkeypatch.setattr(security_tools, "_PRIVATE_ENV_WARNED", False)
    with caplog.at_level("WARNING"):
        assert security_tools._private_ip_block_disabled() is True
    assert "deprecated" in caplog.text


def test_light_sast_no_false_positives_on_typescript_and_fixtures(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "cache.ts").write_text(
        "await redis.multi().set(k, v).exec();\nrequests.push(id);\n"
    )
    (tmp_path / "src" / "__tests__").mkdir()
    (tmp_path / "src" / "__tests__" / "seed.ts").write_text('const password = "hunter2hunter2";\n')
    out = json.loads(repo_risk.invoke({"root": str(tmp_path), "glob": "**/*", "limit": 50}))
    assert out["finding_count"] == 0


def test_light_sast_still_flags_python_patterns_and_optional_test_creds(tmp_path):
    (tmp_path / "app.py").write_text("exec(code)\nrequests.get(url)\n")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_x.py").write_text('password = "hunter2hunter2"\n')
    base = {"root": str(tmp_path), "glob": "**/*.py", "limit": 50}
    patterns = {f["pattern"] for f in json.loads(repo_risk.invoke(base))["findings"]}
    assert {"exec", "requests_no_timeout"} <= patterns
    assert "hardcoded_password" not in patterns
    with_tests = json.loads(repo_risk.invoke({**base, "include_tests": True}))
    assert "hardcoded_password" in {f["pattern"] for f in with_tests["findings"]}


def test_security_sast_rejects_unknown_engine():
    scope = _invoke(security_scope, targets=["file:///tmp"], rationale="x")
    out = _invoke(security_sast, scope_token=scope["scope_token"], engine="bandit")
    assert out["allowed"] == ["light", "semgrep"]


def test_security_sast_semgrep_engine_delegates_to_gateway_and_reports_tool_missing(tmp_path, monkeypatch):
    from xninetzy.ecosystem.scanners import runner

    monkeypatch.setattr(runner, "docker_binary", lambda: None)
    scope = _invoke(security_scope, targets=[f"file://{tmp_path}"], rationale="x")
    out = _invoke(security_sast, scope_token=scope["scope_token"], root=str(tmp_path), engine="semgrep")
    assert out["status"] == runner.STATUS_MISSING


def test_security_sast_default_glob_detects_languages(tmp_path):
    (tmp_path / "api.ts").write_text("export const a = 1;\n")
    (tmp_path / "job.py").write_text("import pickle\npickle.loads(x)\n")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "skip.go").write_text("package x\n")
    scope = _invoke(security_scope, targets=[f"file://{tmp_path}"], rationale="x")
    out = _invoke(security_sast, scope_token=scope["scope_token"], root=str(tmp_path))
    assert out["globs"] == ["**/*.py", "**/*.ts"]
    assert any(f["file"] == "job.py" for f in out["report"]["findings"])


def test_security_sast_explicit_glob_is_respected_and_run_recorded(tmp_path):
    (tmp_path / "job.py").write_text("import pickle\npickle.loads(x)\n")
    scope = _invoke(security_scope, targets=[f"file://{tmp_path}"], rationale="x")
    out = _invoke(security_sast, scope_token=scope["scope_token"], root=str(tmp_path), glob="**/*.py")
    assert out["globs"] == ["**/*.py"]
    from xninetzy.os.security import findings_store

    runs = findings_store.list_runs(scope["scope_token"])
    assert [r["tool"] for r in runs] == ["sast-light"]
    assert runs[0]["hit_count"] == out["report"]["finding_count"]


def test_security_sast_falls_back_to_python_glob_on_empty_repo(tmp_path):
    scope = _invoke(security_scope, targets=[f"file://{tmp_path}"], rationale="x")
    out = _invoke(security_sast, scope_token=scope["scope_token"], root=str(tmp_path))
    assert out["globs"] == ["**/*.py"]


def test_security_sast_marks_light_engine_confidence(tmp_path):
    scope = _invoke(security_scope, targets=[f"file://{tmp_path}"], rationale="x")
    out = _invoke(security_sast, scope_token=scope["scope_token"], root=str(tmp_path))
    assert out["engine"] == "light"
    assert out["confidence"] <= 0.3


def _write_lock_tree(root):
    (root / "package-lock.json").write_text(json.dumps({
        "lockfileVersion": 3,
        "packages": {
            "": {"name": "app"},
            "node_modules/qs": {"version": "6.11.0"},
            "node_modules/@scope/x": {"version": "1.0.0", "dev": True},
        },
    }))
    (root / "bun.lock").write_text(
        '{\n  // c\n  "lockfileVersion": 1,\n  "packages": {\n'
        '    "hono": ["hono@4.6.0", "", {}, "sha"],\n'
        '    "@a/b": ["@a/b@2.0.0", "", {}, "sha"],\n'
        '    "app": ["app@workspace:."],\n  },\n}\n'
    )
    (root / "pnpm-lock.yaml").write_text(
        "lockfileVersion: '9.0'\nimporters:\n  .:\n    x: 1\npackages:\n"
        "  undici@6.1.0:\n    resolution: {}\n  '@scope/pkg@3.2.1(peer@1)':\n    resolution: {}\n"
    )
    (root / "yarn.lock").write_text(
        '# yarn\n\n"esbuild@^0.20.0", esbuild@^0.20.1:\n  version "0.20.2"\n  resolved "x"\n'
        '\nmorgan@^1.10.0:\n  version "1.10.0"\n'
    )
    (root / "uv.lock").write_text('[[package]]\nname = "httpx"\nversion = "0.27.0"\n')
    (root / "poetry.lock").write_text('[[package]]\nname = "flask"\nversion = "3.0.0"\ncategory = "dev"\n')
    (root / "Cargo.lock").write_text('[[package]]\nname = "serde"\nversion = "1.0.0"\n')
    (root / "requirements.txt").write_text("requests==2.31.0\nflask\n# c\n-r other.txt\n")
    (root / "pubspec.lock").write_text('packages:\n  http:\n    dependency: direct\n    version: "1.2.0"\n')
    (root / "go.sum").write_text("golang.org/x/net v0.1.0 h1:a\ngolang.org/x/net v0.1.0/go.mod h1:b\n")
    (root / "composer.lock").write_text(json.dumps({
        "packages": [{"name": "a/b", "version": "v1.0.0"}],
        "packages-dev": [{"name": "c/d", "version": "2.0.0"}],
    }))
    (root / "node_modules").mkdir()
    (root / "node_modules" / "package-lock.json").write_text(json.dumps({"packages": {"node_modules/zzz": {"version": "9.9.9"}}}))


def test_lockfile_parsers_cover_all_formats(tmp_path):
    _write_lock_tree(tmp_path)
    found = {p.name for p in lockfiles.discover(tmp_path)}
    assert "package-lock.json" in found and "go.sum" in found
    by_file: dict[str, set[tuple[str, str]]] = {}
    for path in lockfiles.discover(tmp_path):
        by_file[str(path.relative_to(tmp_path))] = {
            (p.name, p.version) for p in lockfiles.parse_lockfile(path, tmp_path)
        }
    assert by_file["package-lock.json"] == {("qs", "6.11.0"), ("@scope/x", "1.0.0")}
    assert by_file["bun.lock"] == {("hono", "4.6.0"), ("@a/b", "2.0.0")}
    assert by_file["pnpm-lock.yaml"] == {("undici", "6.1.0"), ("@scope/pkg", "3.2.1")}
    assert by_file["yarn.lock"] == {("esbuild", "0.20.2"), ("morgan", "1.10.0")}
    assert by_file["uv.lock"] == {("httpx", "0.27.0")}
    assert by_file["poetry.lock"] == {("flask", "3.0.0")}
    assert by_file["Cargo.lock"] == {("serde", "1.0.0")}
    assert by_file["requirements.txt"] == {("requests", "2.31.0"), ("flask", "unpinned")}
    assert by_file["pubspec.lock"] == {("http", "1.2.0")}
    assert by_file["go.sum"] == {("golang.org/x/net", "v0.1.0")}
    assert by_file["composer.lock"] == {("a/b", "1.0.0"), ("c/d", "2.0.0")}
    assert not any("node_modules" in name for name in by_file)


def test_lockfile_dev_flag_is_reported(tmp_path):
    _write_lock_tree(tmp_path)
    pkgs = {p.name: p.dev for p in lockfiles.parse_lockfile(tmp_path / "package-lock.json", tmp_path)}
    assert pkgs["@scope/x"] is True
    assert pkgs["qs"] is False


def test_security_dependencies_walks_tree_and_states_no_vuln_assessment(tmp_path):
    _write_lock_tree(tmp_path)
    (tmp_path / "services" / "api").mkdir(parents=True)
    (tmp_path / "services" / "api" / "bun.lock").write_text(
        '{"packages": {"hono": ["hono@4.6.0"], "zod": ["zod@3.0.0"]}}'
    )
    scope = _invoke(security_scope, targets=[f"file://{tmp_path}"], rationale="audit")
    out = _invoke(security_dependencies, scope_token=scope["scope_token"], root=str(tmp_path))
    assert out["lockfile_count"] == 12
    assert out["parse_errors"] == []
    assert out["vulnerabilities"] == "NOT_ASSESSED"
    names = {d["name"] for d in out["dependencies"]}
    assert {"qs", "hono", "zod", "undici", "esbuild"} <= names
    assert "zzz" not in names
    assert "security_run_osv" in out["vulnerability_note"]
    from xninetzy.os.security import findings_store

    runs = findings_store.list_runs(scope["scope_token"])
    assert [r["tool"] for r in runs] == ["dependency-inventory"]
    assert runs[0]["hit_count"] == out["dependency_count"]


def test_security_dependencies_reports_corrupt_lockfile(tmp_path):
    (tmp_path / "package-lock.json").write_text("{not json")
    scope = _invoke(security_scope, targets=[f"file://{tmp_path}"], rationale="audit")
    out = _invoke(security_dependencies, scope_token=scope["scope_token"], root=str(tmp_path))
    assert out["parse_errors"][0]["lockfile"] == "package-lock.json"


def test_skill_resource_read_accepts_resource_alias():
    text = skill_resource_read.invoke({"name": "xninetzy-security-testing", "resource": "references/workflow.md"})
    assert "Workflow examples" in text


def test_skill_resource_read_names_expected_parameter_when_missing():
    text = skill_resource_read.invoke({"name": "xninetzy-security-testing"})
    assert "relative_path" in text


def test_file_scope_rejects_parent_of_scope_directory(tmp_path):
    inner = tmp_path / "proj"
    inner.mkdir()
    scope = _invoke(security_scope, targets=[f"file://{inner}"], rationale="audit")
    parent = _invoke(security_dependencies, scope_token=scope["scope_token"], root=str(tmp_path))
    assert "di luar scope" in parent["error"]
    sast = _invoke(security_sast, scope_token=scope["scope_token"], root=str(tmp_path))
    assert "di luar scope" in sast["error"]
    child = inner / "sub"
    child.mkdir()
    assert "error" not in _invoke(security_dependencies, scope_token=scope["scope_token"], root=str(child))
    assert "error" not in _invoke(security_dependencies, scope_token=scope["scope_token"], root=str(inner))
