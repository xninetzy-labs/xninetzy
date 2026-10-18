from __future__ import annotations

import json
import subprocess
import textwrap

import pytest

from xninetzy.ecosystem.scanners import lock as lock_mod
from xninetzy.ecosystem.scanners import runner
from xninetzy.tools.ecosystem import security_review_tools as review
from xninetzy.tools.ecosystem.security_review_tools import (
    scaling_review,
    security_authz_matrix,
    security_compose_review,
    security_nginx_review,
    security_role_paths,
)
from xninetzy.tools.ecosystem.security_tools import security_scope

SDL = textwrap.dedent(
    """
    type Query {
      me: User
      user(id: ID!): User
    }
    type Mutation {
      deleteUser(id: ID!): Boolean
    }
    """
)

COMPOSE = textwrap.dedent(
    """
    services:
      db:
        image: postgres:16
        ports:
          - "5432:5432"
      cache:
        image: redis:7
        ports:
          - "6379:6379"
      agent:
        image: alpine
        privileged: true
        volumes:
          - /var/run/docker.sock:/var/run/docker.sock
    """
)

NGINX = "events {}\nhttp {\n  server {\n    listen 80;\n  }\n}\n"


@pytest.fixture(autouse=True)
def env(tmp_path, monkeypatch):
    monkeypatch.delenv("XNINETZY_ALLOW_PRIVATE_TARGETS", raising=False)
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "t.sqlite3"))
    monkeypatch.setenv("UNTRACKED_OUTPUT_DIR", str(tmp_path / "out"))
    monkeypatch.setattr(runner, "docker_binary", lambda: None)
    monkeypatch.setattr(lock_mod, "default_lock_path", lambda: tmp_path / "security-tools.lock")
    from xninetzy.core.config import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def project(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    (root / "schema.graphql").write_text(SDL)
    (root / "docker-compose.yml").write_text(COMPOSE)
    (root / "nginx.conf").write_text(NGINX)
    return root


@pytest.fixture
def outside(tmp_path):
    root = tmp_path / "outside"
    root.mkdir()
    (root / "schema.graphql").write_text(SDL)
    (root / "docker-compose.yml").write_text(COMPOSE)
    (root / "nginx.conf").write_text(NGINX)
    return root


def _scope(root) -> str:
    return json.loads(security_scope.invoke({"targets": [f"file://{root}"], "rationale": "audit"}))["scope_token"]


def _call(tool, **kwargs) -> dict:
    return json.loads(tool.invoke(kwargs))


def _guard_file(root):
    (root / "setup.test.ts").write_text("export function assertTestDatabase(url: string) { return url.includes('test'); }\n")


def test_authz_matrix_refuses_without_test_database_guard(project):
    out = _call(security_authz_matrix, scope_token=_scope(project), project_root=str(project),
                schema_path=str(project / "schema.graphql"), roles=["USER", "ADMIN"])
    assert "guard" in out["error"]
    assert "matrix" not in out


def test_authz_matrix_builds_matrix_and_skeleton_when_guarded(project):
    _guard_file(project)
    out = _call(security_authz_matrix, scope_token=_scope(project), project_root=str(project),
                schema_path=str(project / "schema.graphql"), roles=["USER", "ADMIN"])
    assert "error" not in out
    assert out["test_database_guard"] == ["setup.test.ts"]
    assert out["operation_count"] == 3
    assert "deleteUser" in out["sensitive_operations"]
    assert any(row["role"] == "ANONYMOUS" for row in out["matrix"])
    assert "bun:test" in out["skeleton"]
    assert all(row["expected"] is None for row in out["matrix"])


def test_authz_matrix_pytest_framework_and_operation_filter(project):
    _guard_file(project)
    out = _call(security_authz_matrix, scope_token=_scope(project), project_root=str(project),
                schema_text=SDL, roles=["USER"], operations=["deleteUser"], framework="pytest")
    assert {row["operation"] for row in out["matrix"]} == {"deleteUser"}
    assert "pytest" in out["skeleton"]


@pytest.mark.parametrize(
    "overrides,fragment",
    [
        ({"target": "production"}, "test"),
        ({"framework": "jest"}, "framework"),
        ({"roles": []}, "roles"),
        ({"operations": ["doesNotExist"]}, "filter"),
    ],
)
def test_authz_matrix_rejects_bad_parameters(project, overrides, fragment):
    _guard_file(project)
    params = {"scope_token": _scope(project), "project_root": str(project), "schema_text": SDL, "roles": ["USER"]}
    params.update(overrides)
    out = _call(security_authz_matrix, **params)
    assert fragment in out["error"]


def test_authz_matrix_rejects_project_root_outside_scope(project, outside):
    _guard_file(outside)
    out = _call(security_authz_matrix, scope_token=_scope(project), project_root=str(outside),
                schema_text=SDL, roles=["USER"])
    assert "di luar scope" in out["error"]


def test_authz_matrix_rejects_schema_path_outside_scope(project, outside):
    _guard_file(project)
    out = _call(security_authz_matrix, scope_token=_scope(project), project_root=str(project),
                schema_path=str(outside / "schema.graphql"), roles=["USER"])
    assert "di luar scope" in out["error"]


def test_authz_matrix_rejects_symlink_escape(project, outside):
    _guard_file(project)
    (project / "link.graphql").symlink_to(outside / "schema.graphql")
    out = _call(security_authz_matrix, scope_token=_scope(project), project_root=str(project),
                schema_path=str(project / "link.graphql"), roles=["USER"])
    assert "di luar scope" in out["error"]


def test_authz_matrix_invalid_guard_pattern_returns_error(project):
    _guard_file(project)
    out = _call(security_authz_matrix, scope_token=_scope(project), project_root=str(project),
                schema_text=SDL, roles=["USER"], guard_pattern="(unclosed")
    assert "regex" in out["error"]


def test_authz_matrix_overlong_guard_pattern_returns_error(project):
    _guard_file(project)
    out = _call(security_authz_matrix, scope_token=_scope(project), project_root=str(project),
                schema_text=SDL, roles=["USER"], guard_pattern="a" * 1000)
    assert "terlalu panjang" in out["error"]


def test_authz_matrix_truncates_large_matrices(project, monkeypatch):
    _guard_file(project)
    monkeypatch.setattr(review, "MAX_MATRIX_ROWS", 3)
    out = _call(security_authz_matrix, scope_token=_scope(project), project_root=str(project),
                schema_text=SDL, roles=["USER", "ADMIN"])
    assert out["truncated"] is True
    assert len(out["matrix"]) == 3


def test_authz_matrix_openapi_json(project):
    _guard_file(project)
    spec = json.dumps({"openapi": "3.0.0", "paths": {"/users/{id}": {"delete": {"operationId": "deleteUser"}}}})
    out = _call(security_authz_matrix, scope_token=_scope(project), project_root=str(project),
                schema_text=spec, roles=["USER"])
    assert out["operation_count"] == 1


def test_authz_matrix_requires_file_scope(project):
    web = json.loads(security_scope.invoke({"targets": ["https://example.com"], "rationale": "own"}))["scope_token"]
    out = _call(security_authz_matrix, scope_token=web, project_root=str(project), schema_text=SDL, roles=["USER"])
    assert "file:" in out["error"]


def test_tools_reject_unknown_scope_token(project):
    out = _call(security_role_paths, scope_token="sec-doesnotexist", root=str(project))
    assert "error" in out


def test_role_paths_scans_inside_scope_and_records_run(project):
    (project / "roles.ts").write_text(
        "export function requireAdmin(user) { return user.isAdmin; }\n"
        "export function promote(user) {\n  requireAdminRole(user);\n  user.role = 'ADMIN';\n}\n"
        "export function sneak(user) {\n  user.role = 'ADMIN';\n}\n"
    )
    token = _scope(project)
    out = _call(security_role_paths, scope_token=token, root=str(project))
    assert out["path_count"] >= 2
    flagged = {p["function"] for p in out["paths"] if p["status"] in {"weaker", "unguarded"}}
    assert "sneak" in flagged


def test_role_paths_rejects_root_outside_scope(project, outside):
    out = _call(security_role_paths, scope_token=_scope(project), root=str(outside))
    assert "di luar scope" in out["error"]


def test_role_paths_rejects_relative_and_missing_roots(project):
    token = _scope(project)
    assert "absolut" in _call(security_role_paths, scope_token=token, root="relative/dir")["error"]
    assert "absolut" in _call(security_role_paths, scope_token=token, root=str(project / "missing"))["error"]


def test_compose_review_finds_issues_and_records_run(project):
    out = _call(security_compose_review, scope_token=_scope(project), path=str(project / "docker-compose.yml"))
    rules = {f["id"] for f in out["findings"]}
    assert {"datastore-exposed", "redis-no-auth", "privileged-container", "docker-socket-mount"} <= rules
    assert out["parsed_with"] == "yaml"
    assert out["by_severity"]["high"] >= 3


def test_compose_review_rejects_outside_scope(project, outside):
    out = _call(security_compose_review, scope_token=_scope(project), path=str(outside / "docker-compose.yml"))
    assert "di luar scope" in out["error"]


def test_compose_review_rejects_oversized_file(project, monkeypatch):
    monkeypatch.setattr(review, "MAX_FILE_BYTES", 10)
    out = _call(security_compose_review, scope_token=_scope(project), path=str(project / "docker-compose.yml"))
    assert "terlalu besar" in out["error"]


def test_compose_review_rejects_unparseable_yaml(project):
    (project / "bad.yml").write_text("services: [unclosed\n  - x: : :")
    out = _call(security_compose_review, scope_token=_scope(project), path=str(project / "bad.yml"))
    assert "tidak dapat di-parse" in out["error"]


def test_compose_review_run_config_falls_back_to_yaml_when_docker_missing(project):
    out = _call(security_compose_review, scope_token=_scope(project), path=str(project / "docker-compose.yml"),
                run_config=True)
    assert out["parsed_with"] == "yaml"


def test_compose_review_run_config_uses_docker_output(project, monkeypatch):
    monkeypatch.setattr(runner, "docker_binary", lambda: "/usr/bin/docker")
    calls = []

    def fake(cmd, **kwargs):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, json.dumps({"services": {"web": {"privileged": True}}}), "")

    monkeypatch.setattr(review, "_EXECUTOR", fake)
    out = _call(security_compose_review, scope_token=_scope(project), path=str(project / "docker-compose.yml"),
                run_config=True)
    assert out["parsed_with"] == "docker compose config"
    assert "--no-interpolate" in calls[0]
    assert "privileged-container" in {f["id"] for f in out["findings"]}


def test_nginx_review_reports_findings(project):
    out = _call(security_nginx_review, scope_token=_scope(project), path=str(project / "nginx.conf"))
    rules = {f["id"] for f in out["findings"]}
    assert {"server-tokens", "no-rate-limit", "missing-security-headers"} <= rules
    assert "nginx_test" not in out


def test_nginx_review_rejects_outside_scope(project, outside):
    out = _call(security_nginx_review, scope_token=_scope(project), path=str(outside / "nginx.conf"))
    assert "di luar scope" in out["error"]


def test_nginx_review_run_test_without_docker_reports_tool_missing(project):
    out = _call(security_nginx_review, scope_token=_scope(project), path=str(project / "nginx.conf"), run_test=True)
    assert out["nginx_test"]["status"] == runner.STATUS_MISSING


def test_nginx_review_run_test_uses_hardened_container(project, monkeypatch):
    monkeypatch.setattr(runner, "docker_binary", lambda: "/usr/bin/docker")
    monkeypatch.setattr(runner, "image_present", lambda image, executor=None: (True, "sha256:abc"))
    seen = []

    def fake(cmd, **kwargs):
        seen.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, "", "syntax is ok")

    monkeypatch.setattr(review, "_EXECUTOR", fake)
    out = _call(security_nginx_review, scope_token=_scope(project), path=str(project / "nginx.conf"), run_test=True)
    joined = " ".join(seen[-1])
    assert "--network none" in joined
    assert "--read-only" in joined
    assert "--cap-drop" in joined
    assert out["nginx_test"]["status"] == runner.STATUS_OK
    assert "syntax is ok" in out["nginx_test"]["output"]


def test_scaling_review_scans_inside_scope(project):
    (project / "app.py").write_text("import asyncio\nfrom collections import defaultdict\nCACHE = {}\n\ndef handler():\n    CACHE['a'] = 1\n")
    out = _call(scaling_review, scope_token=_scope(project), root=str(project), replicas=3, pool_size=20,
                max_connections=50)
    assert "findings" in out
    assert out["finding_count"] == len(out["findings"])


def test_scaling_review_rejects_root_outside_scope(project, outside):
    out = _call(scaling_review, scope_token=_scope(project), root=str(outside))
    assert "di luar scope" in out["error"]
