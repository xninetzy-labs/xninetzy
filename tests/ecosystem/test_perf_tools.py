from __future__ import annotations

import json
import socketserver
import subprocess
import threading

import pytest

from xninetzy.db.sqlite import connect
from xninetzy.ecosystem.scanners import lock as lock_mod
from xninetzy.ecosystem.scanners import runner
from xninetzy.os.insight import postgres_review as pg
from xninetzy.os.insight import redis_review as rd
from xninetzy.tools.ecosystem import perf_tools
from xninetzy.tools.ecosystem.security_tools import security_scope

GIB = 1024 ** 3
MIB = 1024 ** 2
PLAN_OPS = [{"name": "me", "path": "/graphql", "graphql": {"query": "{ me { id } }"}}, {"name": "health", "method": "GET", "path": "/health"}]
K6_EXPORT = {"metrics": {
    "http_reqs": {"count": 6000, "rate": 100.0},
    "http_req_duration": {"avg": 40.0, "med": 35.0, "p(90)": 80.0, "p(95)": 100.0, "p(99)": 200.0, "max": 400.0},
    "http_req_failed": {"value": 0.0},
    "http_req_duration{op:me}": {"avg": 40.0, "med": 35.0, "p(90)": 80.0, "p(95)": 100.0, "p(99)": 200.0, "max": 400.0},
}}


@pytest.fixture(autouse=True)
def env(tmp_path, monkeypatch):
    monkeypatch.delenv("XNINETZY_ALLOW_PRIVATE_TARGETS", raising=False)
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "t.sqlite3"))
    monkeypatch.setenv("UNTRACKED_OUTPUT_DIR", str(tmp_path / "out"))
    monkeypatch.setattr(runner, "docker_binary", lambda: "/usr/bin/docker")
    monkeypatch.setattr(lock_mod, "default_lock_path", lambda: tmp_path / "security-tools.lock")
    monkeypatch.setattr(perf_tools, "_SAMPLER", lambda: 8 * GIB)
    monkeypatch.setattr(perf_tools, "_STATS_SAMPLER", lambda: [{"name": "api", "cpu_pct": 40.0, "mem_mb": 200.0}])
    monkeypatch.setattr(perf_tools, "_WATCHDOG_INTERVAL", 0.01)
    from xninetzy.core.config import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _call(tool, **kw):
    return json.loads(tool.invoke(kw))


def _lab(url="http://127.0.0.1:3000", **extra):
    params = {
        "targets": [url], "rationale": "lab", "kind": "owner_lab", "attestation": "saya pemilik",
        "profile": "active", "active_attestation": "izin aktif", "request_budget": 100000, "rate_per_second": 100,
    }
    params.update(extra)
    return json.loads(security_scope.invoke(params))["scope_token"]


def _used(scope_token):
    with connect() as conn:
        return conn.execute("SELECT requests_used FROM security_scope_labs WHERE scope_token=?", (scope_token,)).fetchone()["requests_used"]


def _plan(name="api-load"):
    return _call(perf_tools.perf_plan, name=name, base_url="http://127.0.0.1:3000", operations=PLAN_OPS)["script_path"]


class FakeProcess:
    def __init__(self, returncode=0, stderr="", wait_for=None):
        self.returncode = returncode
        self._stderr = stderr
        self._wait_for = wait_for

    def communicate(self, timeout=None):
        if self._wait_for is not None:
            assert self._wait_for.wait(5)
            self.returncode = 137
        return "", self._stderr

    def kill(self):
        pass


def _fake_docker(monkeypatch, image_ok=True, returncode=0, write_summary=True, launched=None, killed=None):
    def executor(command, **kwargs):
        if command[1:3] == ["image", "inspect"]:
            return subprocess.CompletedProcess(command, 0 if image_ok else 1, "[]", "" if image_ok else "no such image")
        if command[1] == "kill" and killed is not None:
            killed.set()
        return subprocess.CompletedProcess(command, 0, "", "")

    def popen(command, **kwargs):
        if launched is not None:
            launched.append(command)
        if write_summary:
            for index, part in enumerate(command):
                if part == "-v" and command[index + 1].rsplit(":", 2)[1] == "/out":
                    (perf_tools.Path(command[index + 1].rsplit(":", 2)[0]) / "summary.json").write_text(json.dumps(K6_EXPORT))
        return FakeProcess(returncode, wait_for=killed if killed is not None and not write_summary else None)

    monkeypatch.setattr(perf_tools, "_EXECUTOR", executor)
    monkeypatch.setattr(perf_tools, "_POPEN", popen)


def _run_kwargs(scope, script, **over):
    params = {"scope_token": scope, "script_path": script, "base_url": "http://127.0.0.1:3000", "vus": 10, "duration": "30s", "database_name": "shop_test"}
    params.update(over)
    return params


def test_perf_plan_writes_script_with_slo_and_operations(tmp_path):
    out = _call(perf_tools.perf_plan, name="api-load", base_url="http://127.0.0.1:3000", operations=PLAN_OPS, slo={"p95_ms": 300}, vus=25)
    assert out["operations"] == 2 and out["vus"] == 25 and out["slo"]["p95_ms"] == 300 and out["slo"]["p99_ms"] == 1500
    script = perf_tools.Path(out["script_path"])
    assert script.parent == tmp_path / "out" / "perf" / "scripts"
    assert "p(95)<300" in script.read_text()


def test_perf_plan_from_openapi_and_validation_errors():
    spec = '{"paths": {"/health": {"get": {"operationId": "health"}}, "/users/{id}": {"get": {}}}}'
    assert _call(perf_tools.perf_plan, name="oa", base_url="https://api.example.com", openapi_source=spec)["operations"] == 1
    assert "name" in _call(perf_tools.perf_plan, name="../evil", base_url="http://x", operations=PLAN_OPS)["error"]
    assert "http" in _call(perf_tools.perf_plan, name="ok", base_url="ftp://x", operations=PLAN_OPS)["error"]
    assert "tidak valid" in _call(perf_tools.perf_plan, name="ok", base_url="http://x", operations=[{"name": "a b", "path": "/"}])["error"]
    assert "operations kosong" in _call(perf_tools.perf_plan, name="ok", base_url="http://x")["error"]


def test_perf_run_happy_path_records_run_and_consumes_budget(monkeypatch):
    launched = []
    _fake_docker(monkeypatch, launched=launched)
    scope = _lab()
    out = _call(perf_tools.perf_run_k6, **_run_kwargs(scope, _plan(), vus=10, duration="30s", containers=["api"]))
    assert out["status"] == "OK" and out["label"] == "same-host" and out["same_host"] is True
    assert out["summary"]["overall"]["rps"] == 100.0 and out["watchdog"]["triggered"] is False
    assert out["stats_avg"]["api"]["cpu_pct"] == 40.0
    assert _used(scope) == 300
    command = launched[0]
    assert command[command.index("--network") + 1] == "host" and "--cap-drop=ALL" in command and "--read-only" in command
    assert "BASE_URL=http://127.0.0.1:3000" in command
    stored = perf_tools.Path(perf_tools._perf_root() / "runs" / f"{out['run_id']}.json")
    assert json.loads(stored.read_text())["run_id"] == out["run_id"]


def test_perf_run_requires_active_owner_lab_scope(monkeypatch):
    _fake_docker(monkeypatch)
    script = _plan()
    standard = json.loads(security_scope.invoke({"targets": ["https://example.com"], "rationale": "x"}))["scope_token"]
    assert "owner_lab" in _call(perf_tools.perf_run_k6, **_run_kwargs(standard, script))["error"]
    passive = json.loads(security_scope.invoke({"targets": ["http://127.0.0.1:3000"], "rationale": "lab", "kind": "owner_lab", "attestation": "ok"}))["scope_token"]
    assert "active" in _call(perf_tools.perf_run_k6, **_run_kwargs(passive, script))["error"]
    assert "error" in _call(perf_tools.perf_run_k6, **_run_kwargs("sec-doesnotexist", script))


def test_perf_run_guards_database_target_url_and_script(monkeypatch, tmp_path):
    launched = []
    _fake_docker(monkeypatch, launched=launched)
    scope, script = _lab(), _plan()
    assert "_test" in _call(perf_tools.perf_run_k6, **_run_kwargs(scope, script, database_name="shop_prod"))["error"]
    assert "wajib" in _call(perf_tools.perf_run_k6, **_run_kwargs(scope, script, database_name=" "))["error"]
    assert _call(perf_tools.perf_run_k6, **_run_kwargs(scope, script, database_name="demo", allow_demo_db=True))["status"] == "OK"
    assert "scope" in _call(perf_tools.perf_run_k6, **_run_kwargs(scope, script, base_url="http://127.0.0.1:9999"))["error"]
    outside = tmp_path / "evil.js"
    outside.write_text("export default function () {}")
    assert "perf/scripts" in _call(perf_tools.perf_run_k6, **_run_kwargs(scope, str(outside)))["error"]
    assert len(launched) == 1


@pytest.mark.parametrize(
    "over,fragment",
    [({"vus": 0}, "vus"), ({"vus": 20001}, "vus"), ({"duration": "soon"}, "duration"), ({"duration": "9h"}, "duration"), ({"mem_limit": "lots"}, "mem_limit")],
)
def test_perf_run_validates_bounds(monkeypatch, over, fragment):
    _fake_docker(monkeypatch)
    scope = _lab()
    assert fragment in _call(perf_tools.perf_run_k6, **_run_kwargs(scope, _plan(), **over))["error"]
    assert _used(scope) == 0


def test_perf_run_refuses_when_budget_is_insufficient(monkeypatch):
    launched = []
    _fake_docker(monkeypatch, launched=launched)
    scope = _lab(request_budget=100)
    out = _call(perf_tools.perf_run_k6, **_run_kwargs(scope, _plan(), vus=10, duration="30s"))
    assert "budget" in out["error"] and out["estimated_requests"] == 300
    assert not launched and _used(scope) == 0


def test_perf_run_missing_image_does_not_consume_budget(monkeypatch):
    launched = []
    _fake_docker(monkeypatch, image_ok=False, launched=launched)
    scope = _lab()
    out = _call(perf_tools.perf_run_k6, **_run_kwargs(scope, _plan()))
    assert out["status"] == "TOOL_MISSING" and "docker pull" in out["detail"]
    assert not launched and _used(scope) == 0
    monkeypatch.setattr(runner, "docker_binary", lambda: None)
    assert _call(perf_tools.perf_run_k6, **_run_kwargs(scope, _plan()))["status"] == "TOOL_MISSING"
    assert _used(scope) == 0


def test_perf_run_watchdog_stops_run_below_memory_floor(monkeypatch):
    killed = threading.Event()
    _fake_docker(monkeypatch, write_summary=False, killed=killed)
    monkeypatch.setattr(perf_tools, "_SAMPLER", lambda: 300 * MIB)
    scope = _lab()
    out = _call(perf_tools.perf_run_k6, **_run_kwargs(scope, _plan(), floor_mib=64))
    assert out["status"] == "WATCHDOG_STOPPED" and out["watchdog"]["floor_mib"] == 512
    assert "summary" not in out and killed.is_set()


def test_perf_run_reports_failed_exit(monkeypatch):
    _fake_docker(monkeypatch, returncode=1, write_summary=False)
    out = _call(perf_tools.perf_run_k6, **_run_kwargs(_lab(), _plan()))
    assert out["status"] == "FAILED" and "summary" not in out


def _store_run(run_id, replicas, rps, p95, stats_avg=None):
    runs = perf_tools._perf_root() / "runs"
    runs.mkdir(parents=True, exist_ok=True)
    overall = {"requests": 1, "rps": rps, "error_rate": 0.0, "avg": p95 / 2, "p50": p95 / 2, "p90": p95, "p95": p95, "p99": p95 * 2, "max": p95 * 3}
    payload = {"run_id": run_id, "replicas": replicas, "vus": 100, "same_host": True, "stats_avg": stats_avg or {}, "summary": {"overall": overall, "operations": {}}}
    (runs / f"{run_id}.json").write_text(json.dumps(payload))


def test_perf_compare_and_capacity_use_stored_runs():
    _store_run("run-a", 1, 100.0, 100.0)
    _store_run("run-b", 2, 210.0, 90.0, {"postgres": {"cpu_pct": 150.0, "mem_mb": 1.0}})
    compare = _call(perf_tools.perf_compare, run_a="run-a", run_b="run-b")
    assert compare["overall"]["rps"]["delta_pct"] == 110.0 and compare["same_host"] is True
    capacity = _call(perf_tools.perf_capacity, runs=["run-a", "run-b"])
    assert [r["replicas"] for r in capacity["runs"]] == [1, 2]
    assert capacity["bottleneck"] == "DB CPU" and not capacity["saturation"]["reached"]
    overridden = _call(perf_tools.perf_capacity, runs=["run-a", "run-b"], replicas=[2, 4])
    assert [r["replicas"] for r in overridden["runs"]] == [2, 4]


def test_perf_compare_and_capacity_reject_unknown_or_unsafe_ids():
    _store_run("run-a", 1, 100.0, 100.0)
    assert _call(perf_tools.perf_compare, run_a="run-a", run_b="run-missing")["missing"] == ["run-missing"]
    assert "error" in _call(perf_tools.perf_compare, run_a="../../etc/passwd", run_b="run-a")
    assert "error" in _call(perf_tools.perf_capacity, runs=["run-a", "run-x"])
    assert "sama panjang" in _call(perf_tools.perf_capacity, runs=["run-a"], replicas=[1, 2])["error"]
    assert "kosong" in _call(perf_tools.perf_capacity, runs=[])["error"]
    runs = perf_tools._perf_root() / "runs"
    (runs / "run-nosummary.json").write_text(json.dumps({"run_id": "run-nosummary"}))
    assert "summary" in _call(perf_tools.perf_compare, run_a="run-a", run_b="run-nosummary")["error"]


def test_perf_profile_cpuprofile_stays_inside_output_folder(tmp_path):
    scope = _lab()
    out_dir = tmp_path / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    good = out_dir / "app.cpuprofile"
    good.write_text(json.dumps({"nodes": [{"id": 1, "callFrame": {"functionName": "hot", "url": "a.ts", "lineNumber": 0}}], "samples": [1, 1], "timeDeltas": [1000, 1000]}))
    out = _call(perf_tools.perf_profile, scope_token=scope, runtime="cpuprofile", profile_path=str(good))
    assert out["top_self_time"][0]["frame"].startswith("hot a.ts:1")
    outside = tmp_path / "elsewhere.cpuprofile"
    outside.write_text("{}")
    assert "output" in _call(perf_tools.perf_profile, scope_token=scope, runtime="cpuprofile", profile_path=str(outside))["error"]
    wrong_ext = out_dir / "app.txt"
    wrong_ext.write_text("{}")
    assert "error" in _call(perf_tools.perf_profile, scope_token=scope, runtime="cpuprofile", profile_path=str(wrong_ext))
    broken = out_dir / "broken.cpuprofile"
    broken.write_text("not json")
    assert "parse" in _call(perf_tools.perf_profile, scope_token=scope, runtime="cpuprofile", profile_path=str(broken))["error"]


def test_perf_profile_python_runs_pyspy_in_container(monkeypatch):
    record = []

    def executor(command, **kwargs):
        record.append(command)
        if "record" in command:
            return subprocess.CompletedProcess(command, 0, "", "")
        if "cat" in command:
            return subprocess.CompletedProcess(command, 0, "main;handler;query 30\nmain;render 10\n", "")
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(perf_tools, "_EXECUTOR", executor)
    scope = _lab()
    out = _call(perf_tools.perf_profile, scope_token=scope, runtime="python", service="api", seconds=5)
    assert out["status"] == "OK" and out["top_self_time"][0] == {"frame": "query", "samples": 30, "percent": 75.0}
    assert any(c[:3] == ["docker", "exec", "api"] and "py-spy" in c for c in record)
    assert any("rm" in c for c in record)


def test_perf_profile_python_validates_input_and_reports_missing_tool(monkeypatch):
    scope = _lab()
    assert "service" in _call(perf_tools.perf_profile, scope_token=scope, runtime="python", service="api;rm -rf /")["error"]
    assert "seconds" in _call(perf_tools.perf_profile, scope_token=scope, runtime="python", service="api", seconds=600)["error"]
    assert "runtime" in _call(perf_tools.perf_profile, scope_token=scope, runtime="ruby", service="api")["error"]
    passive = json.loads(security_scope.invoke({"targets": ["http://127.0.0.1:3000"], "rationale": "lab", "kind": "owner_lab", "attestation": "ok"}))["scope_token"]
    assert "active" in _call(perf_tools.perf_profile, scope_token=passive, runtime="python", service="api")["error"]
    monkeypatch.setattr(perf_tools, "_EXECUTOR", lambda command, **kw: subprocess.CompletedProcess(command, 1, "", "executable file not found: py-spy"))
    out = _call(perf_tools.perf_profile, scope_token=scope, runtime="python", service="api")
    assert out["status"] == "TOOL_MISSING" and "SYS_PTRACE" in out["hint"]


class _FakeRedisHandler(socketserver.StreamRequestHandler):
    def _read_command(self):
        header = self.rfile.readline()
        if not header:
            return None
        count = int(header[1:])
        parts = []
        for _ in range(count):
            size = int(self.rfile.readline()[1:])
            parts.append(self.rfile.read(size + 2)[:-2].decode())
        return parts

    def _bulk(self, value):
        data = value.encode()
        return b"$" + str(len(data)).encode() + b"\r\n" + data + b"\r\n"

    def _array(self, items):
        return b"*" + str(len(items)).encode() + b"\r\n" + b"".join(items)

    def handle(self):
        state = self.server.state
        while True:
            command = self._read_command()
            if command is None:
                return
            state["commands"].append(command)
            name = command[0].upper()
            if name == "INFO":
                reply = self._bulk("# Server\r\nredis_version:7.2.4\r\nused_memory:1048576\r\n# Keyspace\r\ndb0:keys=4,expires=1\r\n")
            elif name == "CONFIG":
                key = command[2]
                reply = self._array([self._bulk(key), self._bulk(state["config"].get(key, ""))])
            elif name == "SELECT":
                reply = b"+OK\r\n"
            elif name == "SCAN":
                reply = self._array([self._bulk("0"), self._array([self._bulk(k) for k in state["keys"]])])
            elif name == "TTL":
                reply = b":" + str(state["ttl"].get(command[1], -1)).encode() + b"\r\n"
            elif name == "TYPE":
                reply = b"+list\r\n" if command[1] == "celery" else b"+string\r\n"
            elif name == "MEMORY":
                reply = b":" + str(state["usage"].get(command[2], 100)).encode() + b"\r\n"
            elif name == "AUTH":
                reply = b"+OK\r\n" if command[1] == state["password"] else b"-ERR invalid password\r\n"
            else:
                reply = b"-ERR unknown\r\n"
            self.wfile.write(reply)


@pytest.fixture
def redis_server():
    def start(config, keys, ttl=None, usage=None, password=""):
        server = socketserver.ThreadingTCPServer(("127.0.0.1", 0), _FakeRedisHandler)
        server.daemon_threads = True
        server.state = {"commands": [], "config": config, "keys": keys, "ttl": ttl or {}, "usage": usage or {}, "password": password}
        threading.Thread(target=server.serve_forever, daemon=True).start()
        servers.append(server)
        return server, f"redis://127.0.0.1:{server.server_address[1]}/0"

    servers = []
    yield start
    for server in servers:
        server.shutdown()
        server.server_close()


def test_redis_review_flags_shared_broker_with_eviction_and_stays_read_only(redis_server):
    server, url = redis_server(
        {"maxmemory": "0", "maxmemory-policy": "allkeys-lru", "requirepass": ""},
        ["celery", "cache:user:1", "cache:user:2", "big:blob"],
        ttl={"cache:user:1": 60},
        usage={"big:blob": 5 * MIB},
    )
    scope = _lab(url.replace("redis://", "http://"))
    out = _call(perf_tools.redis_review, scope_token=scope, url=url)
    assert out["status"] == "OK" and out["broker_shared"] is True
    rules = {f["id"] for f in out["findings"]}
    assert {"no-maxmemory", "eviction-drops-broker", "broker-cache-same-db", "no-requirepass", "big-keys"} <= rules
    assert out["databases"]["0"]["ttl_coverage"] == 0.25
    assert out["big_keys"][0]["key"] == "big:blob" and out["server"]["version"] == "7.2.4"
    names = {c[0].upper() for c in server.state["commands"]}
    assert names <= rd.ALLOWED_COMMANDS
    assert not names & {"SET", "DEL", "FLUSHALL", "FLUSHDB", "EXPIRE"}
    assert all(c[1].upper() == "GET" for c in server.state["commands"] if c[0].upper() == "CONFIG")


def test_redis_review_healthy_instance_has_no_findings(redis_server):
    _server, url = redis_server({"maxmemory": "1000000", "maxmemory-policy": "allkeys-lru", "requirepass": "x"}, ["cache:a", "cache:b"], ttl={"cache:a": 10, "cache:b": 10})
    out = _call(perf_tools.redis_review, scope_token=_lab(url.replace("redis://", "http://")), url=url)
    assert out["findings"] == [] and out["broker_shared"] is False


def test_redis_review_requires_loopback_host_in_lab_scope(redis_server):
    _server, url = redis_server({}, [])
    scope = _lab(url.replace("redis://", "http://"))
    assert "loopback" in _call(perf_tools.redis_review, scope_token=scope, url="redis://redis.example.com:6379/0")["error"]
    assert "loopback" in _call(perf_tools.redis_review, scope_token=scope, url="redis://10.0.0.5:6379/0")["error"]
    localhost_url = url.replace("127.0.0.1", "localhost")
    assert "loopback" in _call(perf_tools.redis_review, scope_token=scope, url=localhost_url)["error"]
    assert "redis://" in _call(perf_tools.redis_review, scope_token=scope, url="http://127.0.0.1:1")["error"]
    assert "belum didukung" in _call(perf_tools.redis_review, scope_token=scope, url="rediss://127.0.0.1:1")["error"]


def test_redis_review_reports_unreachable_and_bad_password(redis_server):
    _server, url = redis_server({}, [], password="secret")
    scope = _lab(url.replace("redis://", "http://"))
    assert _call(perf_tools.redis_review, scope_token=scope, url="redis://127.0.0.1:1/0")["status"] == "UNREACHABLE"
    bad = _call(perf_tools.redis_review, scope_token=scope, url=url.replace("//", "//:wrong@"))
    assert bad["status"] in {"FAILED", "UNREACHABLE"}


def test_redis_client_refuses_write_and_unlisted_commands_before_sending(redis_server):
    server, url = redis_server({}, [])
    port = int(url.rsplit(":", 1)[1].split("/")[0])
    client = rd.RedisReadOnly("127.0.0.1", port)
    try:
        for command in (("SET", "a", "b"), ("FLUSHALL",), ("DEL", "a"), ("CONFIG", "SET", "maxmemory", "1"), ("MEMORY", "PURGE"), ("CONFIG",), ("EVAL", "return 1", 0)):
            with pytest.raises(rd.ReadOnlyViolation):
                client.command(*command)
        assert server.state["commands"] == []
        assert client.command("SELECT", 0) == "OK"
    finally:
        client.close()


def test_parse_redis_url_and_info():
    assert rd.parse_redis_url("redis://:p%40ss@127.0.0.1:6380/2") == ("127.0.0.1", 6380, "p@ss", 2)
    assert rd.parse_redis_url("redis://localhost") == ("localhost", 6379, "", 0)
    assert rd.parse_info("# Server\r\nredis_version:7\r\n\r\nused_memory:5\r\n") == {"redis_version": "7", "used_memory": "5"}


SEP = pg.SEP


def _psql(rows_by_marker, record=None, returncode=0, stderr=""):
    def executor(command, **kwargs):
        if record is not None:
            record.append((command, kwargs))
        sql = command[-1]
        if returncode:
            return subprocess.CompletedProcess(command, returncode, "", stderr)
        for marker, rows in rows_by_marker:
            if marker in sql:
                return subprocess.CompletedProcess(command, 0, "\n".join(SEP.join(str(c) for c in row) for row in rows), "")
        return subprocess.CompletedProcess(command, 0, "", "")
    return executor


HEALTHY_ROWS = [
    ("SHOW max_connections", [[100]]),
    ("pg_stat_activity", [["api", "active", 30], ["worker", "idle", 60]]),
    ("pg_extension", [[1]]),
    ("FROM pg_stat_statements", [["SELECT * FROM orders WHERE key='AKIAIOSFODNN7EXAMPLE'", 500, "12000.5", "24.00", 900]]),
    ("pg_stat_user_tables", [["orders", 500, 900000, 10, 50000]]),
]


@pytest.fixture
def psql_present(monkeypatch):
    monkeypatch.setattr(pg.shutil, "which", lambda name: "/usr/bin/psql")


def test_postgres_review_reports_connections_statements_and_index_hints(psql_present, monkeypatch):
    record = []
    monkeypatch.setattr(perf_tools, "_PSQL_EXECUTOR", _psql(HEALTHY_ROWS, record))
    dsn = "postgresql://app:s3cr3tpw@127.0.0.1:5432/shop_test"
    scope = _lab("http://127.0.0.1:3000")
    out = _call(perf_tools.postgres_review, scope_token=scope, dsn=dsn, pool_budget=120)
    assert out["status"] == "OK" and out["max_connections"] == 100
    assert out["connections"]["total"] == 90 and out["connections"]["by_application"] == {"worker": 60, "api": 30}
    rules = {f["id"] for f in out["findings"]}
    assert {"pool-exceeds-max", "connections-near-max", "seq-scan-heavy"} <= rules
    assert out["missing_index_hints"][0]["table"] == "orders"
    assert out["top_statements"][0]["calls"] == 500 and "AKIAIOSFODNN7EXAMPLE" not in out["top_statements"][0]["query"]
    for command, kwargs in record:
        assert "s3cr3tpw" not in " ".join(command)
        assert kwargs["env"]["PGPASSWORD"] == "s3cr3tpw"
        assert "default_transaction_read_only=on" in kwargs["env"]["PGOPTIONS"]
        assert command[-1].lstrip().lower().startswith(("select", "show"))
    assert "s3cr3tpw" not in json.dumps(out)


def test_postgres_review_notes_missing_extension_and_pool_headroom(psql_present, monkeypatch):
    rows = [row for row in HEALTHY_ROWS if row[0] not in {"pg_extension", "pg_stat_user_tables"}]
    rows.insert(2, ("pg_extension", [[0]]))
    monkeypatch.setattr(perf_tools, "_PSQL_EXECUTOR", _psql(rows))
    out = _call(perf_tools.postgres_review, scope_token=_lab(), dsn="postgresql://u:p@127.0.0.1/db", pool_budget=85)
    assert out["top_statements"] == [] and any("pg_stat_statements" in n for n in out["notes"])
    assert {f["id"] for f in out["findings"]} == {"pool-near-max", "connections-near-max"}


def test_postgres_review_requires_loopback_scope_and_valid_dsn(psql_present, monkeypatch):
    monkeypatch.setattr(perf_tools, "_PSQL_EXECUTOR", _psql(HEALTHY_ROWS))
    scope = _lab()
    assert "loopback" in _call(perf_tools.postgres_review, scope_token=scope, dsn="postgresql://u:p@db.example.com/x")["error"]
    assert "loopback" in _call(perf_tools.postgres_review, scope_token=scope, dsn="postgresql://u:p@localhost/x")["error"]
    assert "postgresql" in _call(perf_tools.postgres_review, scope_token=scope, dsn="mysql://u:p@127.0.0.1/x")["error"]


def test_postgres_review_reports_missing_psql_and_redacts_errors(monkeypatch):
    scope = _lab()
    monkeypatch.setattr(pg.shutil, "which", lambda name: None)
    assert _call(perf_tools.postgres_review, scope_token=scope, dsn="postgresql://u:p@127.0.0.1/x")["status"] == "TOOL_MISSING"
    monkeypatch.setattr(pg.shutil, "which", lambda name: "/usr/bin/psql")
    monkeypatch.setattr(perf_tools, "_PSQL_EXECUTOR", _psql([], returncode=2, stderr="FATAL: password authentication failed for user u password=hunter2hunter2"))
    out = _call(perf_tools.postgres_review, scope_token=scope, dsn="postgresql://u:hunter2hunter2@127.0.0.1/x")
    assert out["status"] == "FAILED" and "hunter2hunter2" not in json.dumps(out)


def test_run_sql_refuses_anything_but_select_and_show(psql_present):
    parts = pg.parse_dsn("postgresql://u:p@127.0.0.1/x")
    for statement in ("DROP TABLE users", "UPDATE t SET a=1", "INSERT INTO t VALUES (1)", "  delete from t", "COPY t TO PROGRAM 'x'", "WITH x AS (DELETE FROM t RETURNING 1) SELECT 1"):
        with pytest.raises(pg.PsqlError):
            pg.run_sql(parts, statement, _psql([]))
    assert pg.run_sql(parts, "SHOW max_connections", _psql([("max_connections", [[7]])])) == [["7"]]
