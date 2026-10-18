from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from xninetzy.ecosystem.scanners import adapters, lock as lock_mod, parsers, runner
from xninetzy.ecosystem.scanners.hit import canonical_advisory, make_hit
from xninetzy.tools.ecosystem import security_scanner_tools as tools
from xninetzy.tools.ecosystem.security_tools import security_correlate, security_scope

FAKE_SECRET = "AKIAIOSFODNN7EXAMPLE1234"

GITLEAKS = json.dumps([{"RuleID": "aws-access-token", "File": "src/a.ts", "StartLine": 7, "Secret": FAKE_SECRET, "Match": f"key={FAKE_SECRET}", "Commit": "abcdef1234567890"}])
TRIVY = json.dumps({"Results": [{
    "Target": "bun.lock", "Class": "lang-pkgs",
    "Vulnerabilities": [{"VulnerabilityID": "CVE-2025-0001", "PkgName": "undici", "InstalledVersion": "6.1.0", "FixedVersion": "6.2.0", "Severity": "HIGH", "Title": "undici issue"}],
    "Misconfigurations": [{"ID": "DS002", "Severity": "HIGH", "Title": "root user", "CauseMetadata": {"StartLine": 3}}],
    "Secrets": [{"RuleID": "generic", "Severity": "CRITICAL", "StartLine": 9, "Title": "token", "Match": "***"}],
}]})
OSV = json.dumps({"results": [{"source": {"path": "/src/bun.lock"}, "packages": [{
    "package": {"name": "undici", "version": "6.1.0", "ecosystem": "npm"},
    "vulnerabilities": [{"id": "GHSA-abcd-1234-efgh", "aliases": ["CVE-2025-0001"], "summary": "undici issue", "database_specific": {"severity": "HIGH"}}],
}]}]})
SEMGREP = json.dumps({"results": [{"check_id": "dockerfile.security.missing-user", "path": "Dockerfile", "start": {"line": 4}, "extra": {"severity": "ERROR", "message": "no USER"}}]})
ZAP = json.dumps({"site": [{"@name": "http://localhost:8080", "alerts": [{"pluginid": "10038", "alert": "Content Security Policy Header Not Set", "riskcode": "2", "confidence": "3", "instances": [{"uri": "http://localhost:8080/"}]}]}]})
JUNIT = '<testsuites><testsuite><testcase name="GET /users"><failure message="500 on empty id"/></testcase><testcase name="GET /ok"/></testsuite></testsuites>'
GRYPE = json.dumps({"matches": [{"vulnerability": {"id": "GHSA-abcd-1234-efgh", "severity": "High"}, "relatedVulnerabilities": [{"id": "CVE-2025-0001"}], "artifact": {"name": "undici", "version": "6.1.0"}}]})


def _proc(rc=0, out="", err=""):
    return subprocess.CompletedProcess([], rc, out, err)


def make_executor(outputs: dict[str, str], image_ok=True, digests=("sha256:abc",), record=None, stdouts=None):
    def fake(command, **kwargs):
        if record is not None:
            record.append(command)
        if command[1] == "info":
            return _proc(0, "27.0")
        if command[1:3] == ["image", "inspect"]:
            if not image_ok:
                return _proc(1, "", "No such image")
            return _proc(0, json.dumps([f"img@{d}" for d in digests]))
        if command[1] == "run":
            mounts = {}
            for i, part in enumerate(command):
                if part == "-v":
                    host, container, _mode = command[i + 1].rsplit(":", 2)
                    mounts[container] = host
            out_dir = Path(mounts.get("/out") or mounts["/zap/wrk"])
            stdout = ""
            joined = " ".join(command)
            for image_hint, body in (stdouts or {}).items():
                if image_hint in joined:
                    stdout = body
            for name, body in outputs.items():
                (out_dir / name).write_text(body)
            return _proc(0, stdout)
        return _proc(1, "", "unexpected")
    return fake


@pytest.fixture(autouse=True)
def env(tmp_path, monkeypatch):
    monkeypatch.delenv("XNINETZY_ALLOW_PRIVATE_TARGETS", raising=False)
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "t.sqlite3"))
    monkeypatch.setenv("UNTRACKED_OUTPUT_DIR", str(tmp_path / "out"))
    monkeypatch.setattr(runner, "docker_binary", lambda: "/usr/bin/docker")
    monkeypatch.setattr(lock_mod, "default_lock_path", lambda: tmp_path / "security-tools.lock")
    from xninetzy.core.config import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def repo(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    (root / "a.txt").write_text("x")
    return root


def _scope(repo):
    return json.loads(security_scope.invoke({"targets": [f"file://{repo}"], "rationale": "audit"}))["scope_token"]


def _call(tool, **kw):
    return json.loads(tool.invoke(kw))


def test_parsers_normalize_every_format():
    g = parsers.parse_gitleaks(GITLEAKS)[0]
    assert g.rule == "aws-access-token" and g.line == 7 and FAKE_SECRET not in json.dumps(g.to_dict())
    assert "hash=" in g.evidence
    trivy = parsers.parse_trivy(TRIVY)
    assert {h.category for h in trivy} == {"dependency-vulnerability", "misconfiguration", "hardcoded-secret"}
    assert next(h for h in trivy if h.tool == "trivy" and h.rule == "CVE-2025-0001").extra["fixed_version"] == "6.2.0"
    assert parsers.parse_osv(OSV)[0].extra["advisory"] == "CVE-2025-0001"
    assert parsers.parse_semgrep(SEMGREP)[0].severity == "high"
    assert parsers.parse_zap(ZAP)[0].severity == "medium"
    assert parsers.parse_schemathesis_junit(JUNIT)[0].asset == "GET /users"
    assert parsers.parse_grype(GRYPE)[0].location == "CVE-2025-0001"
    assert parsers.parse_gitleaks("") == [] and parsers.parse_trivy("") == []


def test_advisory_agreement_across_tools_raises_confidence():
    hits = [parsers.parse_trivy(TRIVY)[0], parsers.parse_osv(OSV)[0], parsers.parse_grype(GRYPE)[0]]
    assert {h.asset for h in hits} == {"undici@6.1.0"}
    assert {h.location for h in hits} == {"CVE-2025-0001"}
    out = json.loads(security_correlate.invoke({"hits": [h.to_correlate_input() for h in hits]}))
    assert out["finding_count"] == 1
    assert out["findings"][0]["confidence_tier"] == "high"
    assert out["findings"][0]["scanners"] == ["grype", "osv-scanner", "trivy"]


def test_canonical_advisory_prefers_cve():
    assert canonical_advisory(["GHSA-x", "cve-2024-1", "CVE-2023-9"]) == "CVE-2023-9"
    assert canonical_advisory([]) == "unknown-advisory"


def test_make_hit_redacts_planted_secret_in_evidence():
    hit = make_hit(tool="t", rule="r", severity="high", asset="a", evidence="token sk-abcdefghijklmnop12345 leaked")
    assert "sk-abcdefghijklmnop12345" not in hit.evidence


def test_build_command_is_hardened(tmp_path):
    lock = lock_mod.default_lock()
    lock["tools"]["gitleaks"]["digest"] = "sha256:deadbeef"
    spec = adapters.gitleaks(lock, tmp_path / "src").spec
    command = runner.build_command(spec, tmp_path / "session", uid=1000, gid=1000)
    joined = " ".join(command)
    for flag in ("--read-only", "--cap-drop=ALL", "--security-opt=no-new-privileges", "--pids-limit", "--memory", "--cpus", "--network none"):
        assert flag in joined
    assert "docker.sock" not in joined
    assert command[command.index("--user") + 1] == "1000:1000"
    assert "zricethezav/gitleaks@sha256:deadbeef" in command
    assert f"{tmp_path / 'src'}:/src:ro" in command
    assert f"{tmp_path / 'session'}:/out:rw" in command


def test_docker_socket_mount_is_refused(tmp_path):
    spec = runner.RunSpec(tool="x", image="i", args=[], extra_mounts=[("/var/run/docker.sock", "/var/run/docker.sock", "rw")])
    with pytest.raises(ValueError):
        runner.build_command(spec, tmp_path)
    result = runner.run(spec, tmp_path / "s", executor=make_executor({}))
    assert result.status == runner.STATUS_BLOCKED


def test_image_reference_handles_registry_ports_and_tags():
    assert runner.image_reference("ghcr.io/x/y:v1", "sha256:1") == "ghcr.io/x/y@sha256:1"
    assert runner.image_reference("localhost:5000/x:1", "sha256:1") == "localhost:5000/x@sha256:1"
    assert runner.image_reference("aquasec/trivy:0.74.0", "") == "aquasec/trivy:0.74.0"


def test_missing_image_and_missing_docker_report_tool_missing(repo, monkeypatch):
    scope = _scope(repo)
    monkeypatch.setattr(tools, "_EXECUTOR", make_executor({}, image_ok=False))
    out = _call(tools.security_run_gitleaks, scope_token=scope, root=str(repo))
    assert out["status"] == "TOOL_MISSING" and "docker pull" in out["detail"]
    monkeypatch.setattr(runner, "docker_binary", lambda: None)
    out = _call(tools.security_run_gitleaks, scope_token=scope, root=str(repo))
    assert out["status"] == "TOOL_MISSING"


def test_gitleaks_run_never_returns_the_secret_and_persists_without_duplicates(repo, monkeypatch):
    scope = _scope(repo)
    monkeypatch.setattr(tools, "_EXECUTOR", make_executor({"gitleaks.json": GITLEAKS}))
    first = _call(tools.security_run_gitleaks, scope_token=scope, root=str(repo), persist=True)
    assert first["status"] == "OK" and first["persisted"] == {"created": 1, "seen": 0, "reopened": 0}
    assert FAKE_SECRET not in json.dumps(first)
    second = _call(tools.security_run_gitleaks, scope_token=scope, root=str(repo), persist=True)
    assert second["persisted"] == {"created": 0, "seen": 1, "reopened": 0}
    from xninetzy.os.security import findings_store

    rows = findings_store.list_findings(scope)
    assert len(rows) == 1 and rows[0]["seen_count"] == 2
    assert FAKE_SECRET not in json.dumps(rows)


def test_finding_lifecycle_fixed_then_reopened_on_reappearance(repo, monkeypatch):
    scope = _scope(repo)
    monkeypatch.setattr(tools, "_EXECUTOR", make_executor({}, stdouts={"semgrep/semgrep": SEMGREP}))
    _call(tools.security_run_semgrep, scope_token=scope, root=str(repo), persist=True)
    from xninetzy.os.security import findings_store

    finding_id = findings_store.list_findings(scope)[0]["id"]
    upd = _call(tools.security_finding_update, scope_token=scope, finding_id=finding_id, status="fixed", fix_ref="abc123", regression_test="tests/test_x.py")
    assert upd["status"] == "fixed" and upd["previous_status"] == "open"
    row = findings_store.list_findings(scope)[0]
    assert row["fix_ref"] == "abc123" and row["regression_test"] == "tests/test_x.py"
    again = _call(tools.security_run_semgrep, scope_token=scope, root=str(repo), persist=True)
    assert again["persisted"]["reopened"] == 1
    assert findings_store.list_findings(scope)[0]["status"] == "open"
    assert "error" in _call(tools.security_finding_update, scope_token=scope, finding_id=finding_id, status="bogus")
    assert "error" in _call(tools.security_finding_update, scope_token=scope, finding_id=9999, status="fixed")


def test_source_scanners_refuse_root_outside_scope(repo, tmp_path):
    scope = _scope(repo)
    outside = tmp_path / "other"
    outside.mkdir()
    for fn in (tools.security_run_gitleaks, tools.security_run_trivy, tools.security_run_osv, tools.security_run_semgrep, tools.security_sbom):
        out = _call(fn, scope_token=scope, root=str(outside))
        assert "di luar scope" in out["error"]
        out = _call(fn, scope_token=scope, root=str(tmp_path))
        assert "di luar scope" in out["error"]
    assert "error" in _call(tools.security_run_gitleaks, scope_token=scope, root="relative/dir")
    assert "error" in _call(tools.security_run_gitleaks, scope_token="sec-nope", root=str(repo))


def test_trivy_osv_and_sbom_flow(repo, monkeypatch):
    scope = _scope(repo)
    monkeypatch.setattr(tools, "_EXECUTOR", make_executor({"trivy.json": TRIVY}))
    trivy = _call(tools.security_run_trivy, scope_token=scope, root=str(repo))
    assert trivy["hit_count"] == 3 and trivy["by_severity"]["critical"] == 1
    monkeypatch.setattr(tools, "_EXECUTOR", make_executor({}, stdouts={"osv-scanner": OSV}))
    osv = _call(tools.security_run_osv, scope_token=scope, root=str(repo))
    assert osv["hits"][0]["extra"]["advisory"] == "CVE-2025-0001"
    monkeypatch.setattr(tools, "_EXECUTOR", make_executor({}, stdouts={"anchore/syft": json.dumps({"components": [{}, {}]}), "anchore/grype": GRYPE}))
    sbom = _call(tools.security_sbom, scope_token=scope, root=str(repo))
    assert sbom["sbom_components"] == 2 and sbom["hit_count"] == 1


def test_bad_output_is_reported_not_swallowed(repo, monkeypatch):
    scope = _scope(repo)
    monkeypatch.setattr(tools, "_EXECUTOR", make_executor({"trivy.json": "{not json"}))
    out = _call(tools.security_run_trivy, scope_token=scope, root=str(repo))
    assert out["status"] == "FAILED" and "parse" in out["detail"]
    monkeypatch.setattr(tools, "_EXECUTOR", make_executor({}))
    out = _call(tools.security_run_trivy, scope_token=scope, root=str(repo))
    assert out["status"] == "FAILED" and "output" in out["detail"]


def test_invalid_modes_are_rejected(repo):
    scope = _scope(repo)
    assert "mode" in _call(tools.security_run_gitleaks, scope_token=scope, root=str(repo), mode="x")["error"]
    assert "mode" in _call(tools.security_run_trivy, scope_token=scope, root=str(repo), mode="image")["error"]


def test_check_tools_states(monkeypatch):
    monkeypatch.setattr(tools, "_EXECUTOR", make_executor({}, image_ok=False))
    out = _call(tools.security_check_tools)
    assert out["summary"]["MISSING"] == len(out["tools"])
    monkeypatch.setattr(tools, "_EXECUTOR", make_executor({}))
    out = _call(tools.security_check_tools)
    assert out["summary"]["DEGRADED"] == len(out["tools"])
    pinned = _call(tools.security_check_tools, pin=True)
    assert len(pinned["pinned"]) == len(pinned["tools"])
    ready = _call(tools.security_check_tools)
    assert ready["summary"]["READY"] == len(ready["tools"])
    monkeypatch.setattr(tools, "_EXECUTOR", make_executor({}, digests=("sha256:other",)))
    assert _call(tools.security_check_tools)["summary"]["DEGRADED"] == len(ready["tools"])
    monkeypatch.setattr(runner, "docker_binary", lambda: None)
    assert _call(tools.security_check_tools)["summary"]["UNHEALTHY"] == len(ready["tools"])


def test_lab_scope_gates_zap_and_uses_host_network(monkeypatch):
    lab = json.loads(security_scope.invoke({
        "targets": ["http://localhost:8080"], "rationale": "lab", "kind": "owner_lab",
        "attestation": "saya pemilik", "request_budget": 2000,
    }))
    commands: list = []
    monkeypatch.setattr(tools, "_EXECUTOR", make_executor({"zap.json": ZAP}, record=commands))
    out = _call(tools.security_run_zap, scope_token=lab["scope_token"], target="http://localhost:8080")
    assert out["status"] == "OK" and out["hits"][0]["rule"] == "10038"
    run_cmd = next(c for c in commands if c[1] == "run")
    assert run_cmd[run_cmd.index("--network") + 1] == "host"
    again = _call(tools.security_run_zap, scope_token=lab["scope_token"], target="http://localhost:8080")
    assert "budget" in again["error"]
    api = _call(tools.security_run_zap, scope_token=lab["scope_token"], target="http://localhost:8080", mode="api", schema_path="http://localhost:8080/openapi.json")
    assert "active" in api["error"]
    assert "error" in _call(tools.security_run_zap, scope_token=lab["scope_token"], target="http://localhost:9999")


def test_zap_baseline_on_standard_scope_uses_bridge(monkeypatch):
    scope = json.loads(security_scope.invoke({"targets": ["https://example.com"], "rationale": "own site"}))["scope_token"]
    commands: list = []
    monkeypatch.setattr(tools, "_EXECUTOR", make_executor({"zap.json": ZAP}, record=commands))
    out = _call(tools.security_run_zap, scope_token=scope, target="https://example.com")
    assert out["status"] == "OK"
    run_cmd = next(c for c in commands if c[1] == "run")
    assert run_cmd[run_cmd.index("--network") + 1] == "bridge"
    assert "error" in _call(tools.security_run_zap, scope_token=scope, target="https://example.com", mode="api", schema_path="x")


def test_schemathesis_requires_schema_on_same_origin(monkeypatch):
    lab = json.loads(security_scope.invoke({"targets": ["http://localhost:8080"], "rationale": "lab", "kind": "owner_lab", "attestation": "ok"}))
    monkeypatch.setattr(tools, "_EXECUTOR", make_executor({"schemathesis.xml": JUNIT}))
    bad = _call(tools.security_run_schemathesis, scope_token=lab["scope_token"], target="http://localhost:8080", schema_url="http://localhost:9000/openapi.json")
    assert "error" in bad
    good = _call(tools.security_run_schemathesis, scope_token=lab["scope_token"], target="http://localhost:8080", schema_url="http://localhost:8080/openapi.json", max_examples=9999)
    assert good["status"] == "OK" and good["hit_count"] == 1


def test_report_lists_tools_findings_passed_checks_and_limitations(repo, monkeypatch):
    scope = _scope(repo)
    monkeypatch.setattr(tools, "_EXECUTOR", make_executor({"gitleaks.json": GITLEAKS}))
    _call(tools.security_run_gitleaks, scope_token=scope, root=str(repo), persist=True)
    monkeypatch.setattr(tools, "_EXECUTOR", make_executor({"trivy.json": json.dumps({"Results": []})}))
    _call(tools.security_run_trivy, scope_token=scope, root=str(repo))
    monkeypatch.setattr(tools, "_EXECUTOR", make_executor({}, image_ok=False))
    _call(tools.security_run_osv, scope_token=scope, root=str(repo))
    out = _call(tools.security_report, scope_token=scope)
    md = out["markdown"]
    assert "| gitleaks | 8.30.1 | 1 | OK |" in md
    assert "## Suspected findings" in md and "aws-access-token" in md
    assert "trivy on" in md.split("## Passed checks")[1]
    assert "osv-scanner: TOOL_MISSING" in md
    assert FAKE_SECRET not in md
    assert Path(out["path"]).read_text() == md
    assert "error" in _call(tools.security_report, scope_token="sec-nope")


TRIVY_WITH_CONTEXT = json.dumps({"Results": [{"Target": "config.ts", "Secrets": [{
    "RuleID": "github-pat", "Severity": "CRITICAL", "Title": "GitHub PAT", "StartLine": 3,
    "Match": "github = \"ghp_012345678901234567890123456789abcdef\"",
    "Code": {"Lines": [{"Number": 1, "Content": "const aws_secret = \"wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY\";"}]},
}]}]})


def test_raw_scanner_output_on_disk_is_sanitized(repo, monkeypatch):
    scope = _scope(repo)
    monkeypatch.setattr(tools, "_EXECUTOR", make_executor({"trivy.json": TRIVY_WITH_CONTEXT}))
    out = _call(tools.security_run_trivy, scope_token=scope, root=str(repo))
    assert out["hit_count"] == 1
    raw = Path(out["output_path"]).read_text()
    assert "wJalrXUtnFEMI" not in raw and "ghp_0123456789" not in raw
    assert json.loads(raw)["Results"][0]["Secrets"][0]["RuleID"] == "github-pat"
    assert "wJalrXUtnFEMI" not in json.dumps(out)


def test_sanitize_raw_output_handles_non_json_and_empty():
    from xninetzy.ecosystem.scanners.hit import sanitize_raw_output

    assert sanitize_raw_output("") == ""
    assert "sk-abcdefghijklmnop12345" not in sanitize_raw_output("<x>sk-abcdefghijklmnop12345</x>")
