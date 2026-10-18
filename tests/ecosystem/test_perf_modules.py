from __future__ import annotations

import json
import shutil
import subprocess
import threading
import time

import pytest

from xninetzy.ecosystem.scanners import lock as lock_mod
from xninetzy.ecosystem.scanners import runner
from xninetzy.os.perf import k6_run, k6_script, stats, watchdog

MIB = 1024 * 1024
GIB = 1024 * MIB

OPERATIONS = [
    {"name": "me", "path": "/graphql", "graphql": {"query": "{ me { id } }"}, "weight": 3},
    {"name": "health", "method": "GET", "path": "/health"},
    {"name": "create", "method": "POST", "path": "/items", "body": {"a": 1}, "headers": {"X-Test": "1"}},
]


def _summary(rps, p95, error=0.0, ops=None, p50=None, p99=None):
    overall = {"requests": int(rps * 60), "rps": rps, "error_rate": error, "avg": p95 / 2, "p50": p50 or p95 / 2, "p90": p95 * 0.9, "p95": p95, "p99": p99 or p95 * 2, "max": p95 * 3}
    return {"overall": overall, "operations": ops or {}}


def _k6_export(rps=100.0, p95=120.0, failed=0.0, ops=("me",)):
    trend = {"avg": 50.0, "med": 40.0, "p(90)": p95 * 0.9, "p(95)": p95, "p(99)": p95 * 2, "max": p95 * 3}
    metrics = {
        "http_reqs": {"count": int(rps * 60), "rate": rps},
        "http_req_duration": trend,
        "http_req_failed": {"value": failed, "passes": 0, "fails": 10},
    }
    for op in ops:
        metrics[f"http_req_duration{{op:{op}}}"] = trend
        metrics[f"http_reqs{{op:{op}}}"] = {"count": 10, "rate": rps / 2}
        metrics[f"http_req_failed{{op:{op}}}"] = {"value": failed}
    return {"metrics": metrics}


def test_render_script_has_tags_thresholds_and_stages():
    script = k6_script.render_k6_script("http://127.0.0.1:3000/", OPERATIONS, vus=50, ramp="10s", hold="1m", down="5s")
    assert 'import http from "k6/http";' in script
    assert '"http://127.0.0.1:3000"' in script
    assert "tags: { op: op.name }" in script
    for op in ("me", "health", "create"):
        assert f"http_req_duration{{op:{op}}}" in script
    assert "p(95)<500" in script and "p(99)<1500" in script and "rate<0.01" in script
    assert '"target": 50' in script and '"duration": "1m"' in script and '"target": 0' in script
    assert "sleep(THINK_MIN" in script


def test_render_script_custom_slo_overrides_defaults():
    script = k6_script.render_k6_script("http://x", OPERATIONS[:2], slo={"p95_ms": 200, "error_rate": 0.05})
    assert "p(95)<200" in script and "rate<0.05" in script and "p(99)<1500" in script


@pytest.mark.parametrize(
    "operations,kwargs",
    [
        ([], {}),
        ([{"name": "bad name", "path": "/x"}], {}),
        ([{"name": "a", "path": "x"}], {}),
        ([{"name": "a", "path": "/x", "method": "TRACE"}], {}),
        ([{"name": "a", "path": "/x", "weight": 0}], {}),
        ([{"name": "a", "path": "/x"}, {"name": "a", "path": "/y"}], {}),
        ([{"name": "a", "path": "/x"}], {"vus": 0}),
        ([{"name": "a", "path": "/x"}], {"vus": k6_script.MAX_VUS + 1}),
        ([{"name": "a", "path": "/x"}], {"ramp": "soon"}),
        ([{"name": "a", "path": "/x"}], {"think_min": 5, "think_max": 1}),
    ],
)
def test_render_script_rejects_invalid_plans(operations, kwargs):
    with pytest.raises(k6_script.PlanError):
        k6_script.render_k6_script("http://x", operations, **kwargs)


def test_render_script_neutralizes_hostile_strings():
    url = "http://x\"; evil(); #"
    hostile = [{"name": "ok", "path": "/x", "headers": {"X": "\"; process.exit(1); #"}}]
    script = k6_script.render_k6_script(url, hostile)
    line = next(row for row in script.splitlines() if row.startswith("const BASE_URL"))
    literal = line.split("||", 1)[1].strip().rstrip(";")
    assert json.loads(literal) == url
    operations_json = script.split("const OPERATIONS = ", 1)[1].split(";\nconst THINK_MIN", 1)[0]
    assert json.loads(operations_json)[0]["headers"]["X"] == "\"; process.exit(1); #"


@pytest.mark.skipif(shutil.which("node") is None, reason="node tidak terpasang")
def test_generated_script_is_syntactically_valid_javascript(tmp_path):
    script = k6_script.render_k6_script("http://127.0.0.1:3000", OPERATIONS)
    target = tmp_path / "plan.mjs"
    target.write_text(script, encoding="utf-8")
    proc = subprocess.run(["node", "--check", str(target)], capture_output=True, text=True, timeout=30, check=False)
    assert proc.returncode == 0, proc.stderr


def test_operations_derived_from_openapi_skip_parameterised_paths():
    spec = {"paths": {
        "/health": {"get": {"operationId": "health"}},
        "/users": {"get": {}},
        "/users/{id}": {"get": {}},
        "/search": {"get": {"parameters": [{"name": "q", "required": True}]}},
        "/items": {"post": {}},
    }}
    ops = k6_script.derive_operations_from_openapi(spec)
    assert [o["name"] for o in ops] == ["health", "GET_users"]
    assert all(o["method"] == "GET" for o in ops)


def test_effective_floor_enforces_minimum_and_default():
    assert watchdog.effective_floor(None) == watchdog.DEFAULT_FLOOR_BYTES == int(1.5 * GIB)
    assert watchdog.effective_floor(0) == watchdog.DEFAULT_FLOOR_BYTES
    assert watchdog.effective_floor(100 * MIB) == watchdog.MIN_FLOOR_BYTES == 512 * MIB
    assert watchdog.effective_floor(4 * GIB) == 4 * GIB


def test_read_mem_available_parses_meminfo(tmp_path):
    meminfo = tmp_path / "meminfo"
    meminfo.write_text("MemTotal: 16000000 kB\nMemAvailable:    2048000 kB\n")
    assert watchdog.read_mem_available(str(meminfo)) == 2048000 * 1024
    meminfo.write_text("MemTotal: 1 kB\n")
    with pytest.raises(RuntimeError):
        watchdog.read_mem_available(str(meminfo))


def test_parse_docker_stats_handles_units_and_garbage():
    rows = watchdog.parse_docker_stats("api,12.5%,300MiB / 2GiB\ndb,3%,1.5GiB / 4GiB\nbroken\nbad,notpct,1MiB / 2MiB\n")
    assert rows == [{"name": "api", "cpu_pct": 12.5, "mem_mb": 300.0}, {"name": "db", "cpu_pct": 3.0, "mem_mb": 1536.0}]


def test_watchdog_triggers_below_floor_and_stops_once():
    stopped = threading.Event()
    calls = []
    dog = watchdog.Watchdog(
        2 * GIB, lambda: (calls.append(1), stopped.set()), interval=0.01,
        sampler=lambda: 600 * MIB,
    )
    dog.start()
    assert stopped.wait(3)
    dog.finish()
    assert dog.triggered and calls == [1]
    assert "600 MiB" in dog.reason and "2048 MiB" in dog.reason
    assert dog.report()["floor_mib"] == 2048


def test_watchdog_clamps_requested_floor_to_512_mib():
    stopped = threading.Event()
    dog = watchdog.Watchdog(64 * MIB, stopped.set, interval=0.01, sampler=lambda: 300 * MIB)
    dog.start()
    assert stopped.wait(3)
    dog.finish()
    assert dog.floor == 512 * MIB and dog.triggered


def test_watchdog_stays_quiet_when_memory_is_healthy_and_collects_stats():
    stopped = threading.Event()
    dog = watchdog.Watchdog(
        1 * GIB, stopped.set, interval=0.01, sampler=lambda: 8 * GIB,
        stats_sampler=lambda: [{"name": "api", "cpu_pct": 10.0, "mem_mb": 100.0}],
    )
    dog.start()
    time.sleep(0.15)
    dog.finish()
    assert not dog.triggered and not stopped.is_set()
    assert dog.samples >= 2 and len(dog.stats) >= 2 and dog.stats[0]["name"] == "api"
    assert dog.report()["min_available_mib"] == 8192


def test_watchdog_stops_when_sampler_fails():
    stopped = threading.Event()

    def broken():
        raise OSError("no /proc")

    dog = watchdog.Watchdog(None, stopped.set, interval=0.01, sampler=broken)
    dog.start()
    assert stopped.wait(3)
    dog.finish()
    assert dog.triggered and "sampler gagal" in dog.reason


def test_parse_k6_summary_extracts_overall_and_per_operation():
    parsed = stats.parse_k6_summary(_k6_export(rps=80.0, p95=150.0, failed=0.02, ops=("me", "health")))
    assert parsed["overall"]["rps"] == 80.0 and parsed["overall"]["p95"] == 150.0 and parsed["overall"]["error_rate"] == 0.02
    assert set(parsed["operations"]) == {"health", "me"}
    assert parsed["operations"]["me"]["p50"] == 40.0 and parsed["operations"]["me"]["requests"] == 10
    assert stats.parse_k6_summary({})["overall"]["requests"] == 0


def test_compare_summaries_reports_delta_and_missing_operations():
    a = _summary(100, 200, ops={"me": {"rps": 50, "p95": 200}, "gone": {"rps": 1}})
    b = _summary(150, 150, ops={"me": {"rps": 80, "p95": 100}, "new": {"rps": 2}})
    out = stats.compare_summaries(a, b)
    assert out["overall"]["rps"] == {"a": 100.0, "b": 150.0, "delta": 50.0, "delta_pct": 50.0}
    assert out["overall"]["p95"]["delta_pct"] == -25.0
    assert out["operations"]["me"]["rps"]["delta_pct"] == 60.0
    assert out["only_in_a"] == ["gone"] and out["only_in_b"] == ["new"]
    assert out["overall"]["error_rate"]["delta_pct"] is None


def test_average_stats_groups_by_container():
    rows = [{"name": "api", "cpu_pct": 10, "mem_mb": 100}, {"name": "api", "cpu_pct": 30, "mem_mb": 300}, {"name": "db", "cpu_pct": 5, "mem_mb": 50}]
    assert stats.average_stats(rows) == {
        "api": {"cpu_pct": 20.0, "mem_mb": 200.0, "samples": 2},
        "db": {"cpu_pct": 5.0, "mem_mb": 50.0, "samples": 1},
    }


@pytest.mark.parametrize(
    "name,category",
    [("xn-k6-run", "generator"), ("app-postgres-1", "database"), ("redis", "cache"), ("nginx-edge", "proxy"), ("graphql-api", "api"), ("mystery", "other")],
)
def test_categorize_containers(name, category):
    assert stats.categorize(name) == category


def _run(replicas, rps, p95, stats_avg=None, same_host=True):
    return {"run_id": f"run-{replicas}", "replicas": replicas, "vus": 100, "same_host": same_host, "stats_avg": stats_avg or {}, "summary": _summary(rps, p95)}


def test_capacity_detects_saturation_from_flat_throughput():
    report = stats.capacity_report([_run(1, 100, 100), _run(2, 190, 110), _run(4, 200, 130)])
    assert [r["replicas"] for r in report["runs"]] == [1, 2, 4]
    assert report["runs"][1]["efficiency"] == 0.95
    assert report["saturation"]["reached"] and report["saturation"]["at_replicas"] == 4
    assert "gain" in report["saturation"]["reason"]


def test_capacity_detects_saturation_from_slo_breach():
    report = stats.capacity_report([_run(1, 100, 100), _run(2, 190, 900)], slo_p95_ms=500)
    assert report["saturation"]["reached"] and "above SLO" in report["saturation"]["reason"]


def test_capacity_reports_no_saturation_and_names_bottleneck():
    avg = {"api-1": {"cpu_pct": 40.0, "mem_mb": 1}, "postgres": {"cpu_pct": 180.0, "mem_mb": 1}, "xn-k6-x": {"cpu_pct": 30.0, "mem_mb": 1}}
    report = stats.capacity_report([_run(1, 100, 100), _run(2, 195, 105, avg)])
    assert not report["saturation"]["reached"]
    assert report["bottleneck"] == "DB CPU"
    assert any("same-host" in note for note in report["notes"])


def test_capacity_flags_generator_as_bottleneck_when_it_rivals_the_top_consumer():
    avg = {"api": {"cpu_pct": 100.0, "mem_mb": 1}, "xn-k6-x": {"cpu_pct": 90.0, "mem_mb": 1}}
    assert stats.capacity_report([_run(1, 100, 100, avg)])["bottleneck"] == "generator CPU on the same host"


def test_capacity_without_stats_says_so_and_rejects_empty_input():
    report = stats.capacity_report([_run(1, 100, 100, same_host=False)])
    assert report["bottleneck"] == "unknown" and any("no docker stats" in n for n in report["notes"])
    with pytest.raises(ValueError):
        stats.capacity_report([])


def test_top_self_time_pyspy_raw_ranks_leaf_frames():
    raw = "main;handler;query 30\nmain;handler;render 10\nmain;other;query 20\nnot a line\n"
    top = stats.top_self_time_pyspy_raw(raw, 2)
    assert top[0] == {"frame": "query", "samples": 50, "percent": 83.33}
    assert top[1]["frame"] == "render" and len(top) == 2


def test_top_self_time_cpuprofile_aggregates_by_function():
    profile = {
        "nodes": [
            {"id": 1, "callFrame": {"functionName": "hot", "url": "file:///a.ts", "lineNumber": 9}},
            {"id": 2, "callFrame": {"functionName": "", "url": "", "lineNumber": -1}},
        ],
        "samples": [1, 1, 2],
        "timeDeltas": [3000, 3000, 2000],
    }
    top = stats.top_self_time_cpuprofile(json.dumps(profile), 5)
    assert top[0]["frame"] == "hot file:///a.ts:10" and top[0]["self_ms"] == 6.0 and top[0]["percent"] == 75.0
    assert top[1]["frame"].startswith("(anonymous)")
    with pytest.raises(ValueError):
        stats.top_self_time_cpuprofile("not json")


class FakeProcess:
    def __init__(self, on_communicate, returncode=0):
        self._on_communicate = on_communicate
        self.returncode = returncode
        self.killed = False

    def communicate(self, timeout=None):
        return self._on_communicate(self)

    def kill(self):
        self.killed = True


def _mount(command, container):
    for index, part in enumerate(command):
        if part == "-v":
            host, target, _mode = command[index + 1].rsplit(":", 2)
            if target == container:
                return host
    raise AssertionError(f"mount {container} tidak ada")


@pytest.fixture
def k6_env(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "docker_binary", lambda: "/usr/bin/docker")
    script = tmp_path / "scripts" / "plan.js"
    script.parent.mkdir()
    script.write_text("export default function () {}")
    spec = k6_run.build_spec(lock_mod.default_lock(), script, "http://127.0.0.1:3000", 10, "30s", "1g", "xn-k6-test")
    return spec, tmp_path / "run"


def _executor(record, image_ok=True):
    def fake(command, **kwargs):
        record.append(command)
        if command[1:3] == ["image", "inspect"]:
            return subprocess.CompletedProcess(command, 0 if image_ok else 1, "[]", "" if image_ok else "no such image")
        return subprocess.CompletedProcess(command, 0, "", "")
    return fake


def test_build_spec_is_hardened_and_pins_target_env(k6_env):
    spec, run_dir = k6_env
    command = runner.build_command(spec, run_dir, uid=1000, gid=1000)
    assert command[:3] == ["docker", "run", "--rm"]
    for flag in ("--cap-drop=ALL", "--security-opt=no-new-privileges", "--read-only"):
        assert flag in command
    assert command[command.index("--user") + 1] == "1000:1000"
    assert command[command.index("--memory") + 1] == "1g"
    assert command[command.index("--network") + 1] == "host"
    assert "BASE_URL=http://127.0.0.1:3000" in command
    assert _mount(command, "/scripts") == str(spec.extra_mounts[0][0])
    assert f"{spec.extra_mounts[0][0]}:/scripts:ro" in command
    assert not any("docker.sock" in part for part in command)
    assert command[command.index("--name") + 1] == "xn-k6-test"


def test_execute_reports_ok_with_parsed_summary_and_stats(k6_env):
    spec, run_dir = k6_env
    calls = []

    def popen(command, **kwargs):
        (run_dir / "summary.json").write_text(json.dumps(_k6_export(rps=90.0, p95=110.0)))
        return FakeProcess(lambda proc: ("", ""), 0)

    result = k6_run.execute(
        spec, run_dir, 512 * MIB, ["xn-k6-test"], popen=popen, executor=_executor(calls),
        sampler=lambda: 8 * GIB, interval=0.01,
        stats_sampler=lambda: [{"name": "xn-k6-test", "cpu_pct": 50.0, "mem_mb": 200.0}],
    )
    assert result["status"] == k6_run.STATUS_OK and result["returncode"] == 0
    assert result["summary"]["overall"]["rps"] == 90.0
    assert result["watchdog"]["triggered"] is False
    assert "xn-k6-test" in result["stats_avg"]
    assert (run_dir / "docker-stats.csv").read_text().splitlines()[0] == "t,name,cpu_pct,mem_mb"


def test_execute_maps_exit_99_to_thresholds_failed(k6_env):
    spec, run_dir = k6_env

    def popen(command, **kwargs):
        (run_dir / "summary.json").write_text(json.dumps(_k6_export()))
        return FakeProcess(lambda proc: ("", ""), 99)

    result = k6_run.execute(spec, run_dir, None, [], popen=popen, executor=_executor([]), sampler=lambda: 8 * GIB, interval=0.01, stats_sampler=lambda: [])
    assert result["status"] == k6_run.STATUS_THRESHOLDS and "summary" in result


def test_execute_fails_without_summary_or_on_bad_exit(k6_env):
    spec, run_dir = k6_env
    kwargs = dict(executor=_executor([]), sampler=lambda: 8 * GIB, interval=0.01, stats_sampler=lambda: [])
    no_summary = k6_run.execute(spec, run_dir, None, [], popen=lambda c, **k: FakeProcess(lambda p: ("", ""), 0), **kwargs)
    assert no_summary["status"] == runner.STATUS_FAILED and "summary.json" in no_summary["detail"]
    crashed = k6_run.execute(spec, run_dir, None, [], popen=lambda c, **k: FakeProcess(lambda p: ("", "boom"), 1), **kwargs)
    assert crashed["status"] == runner.STATUS_FAILED and crashed["stderr"] == "boom"


def test_execute_watchdog_kills_container_and_reports_stop(k6_env):
    spec, run_dir = k6_env
    killed = threading.Event()
    record = []

    def executor(command, **kwargs):
        record.append(command)
        if command[1:3] == ["image", "inspect"]:
            return subprocess.CompletedProcess(command, 0, "[]", "")
        if command[1] == "kill":
            killed.set()
        return subprocess.CompletedProcess(command, 0, "", "")

    def communicate(proc):
        assert killed.wait(5)
        proc.returncode = 137
        return "", ""

    result = k6_run.execute(
        spec, run_dir, 2 * GIB, [], popen=lambda c, **k: FakeProcess(communicate), executor=executor,
        sampler=lambda: 700 * MIB, interval=0.01, stats_sampler=lambda: [],
    )
    assert result["status"] == k6_run.STATUS_WATCHDOG
    assert result["watchdog"]["triggered"] and "700 MiB" in result["detail"]
    assert ["docker", "kill", "xn-k6-test"] in record
    assert "summary" not in result


def test_execute_timeout_kills_container(k6_env):
    spec, run_dir = k6_env
    spec.timeout = 1
    record = []
    state = {"first": True}

    def communicate(proc):
        if state["first"]:
            state["first"] = False
            raise subprocess.TimeoutExpired("docker", 1)
        return "", ""

    process = FakeProcess(communicate)
    result = k6_run.execute(spec, run_dir, None, [], popen=lambda c, **k: process, executor=_executor(record), sampler=lambda: 8 * GIB, interval=0.01, stats_sampler=lambda: [])
    assert result["status"] == runner.STATUS_TIMEOUT and process.killed
    assert ["docker", "kill", "xn-k6-test"] in record


def test_execute_reports_missing_image_and_docker_without_running(k6_env, monkeypatch):
    spec, run_dir = k6_env
    launched = []
    missing = k6_run.execute(spec, run_dir, None, [], popen=lambda c, **k: launched.append(c), executor=_executor([], image_ok=False), sampler=lambda: 8 * GIB, stats_sampler=lambda: [])
    assert missing["status"] == runner.STATUS_MISSING and "docker pull" in missing["detail"] and not launched
    monkeypatch.setattr(runner, "docker_binary", lambda: None)
    no_docker = k6_run.execute(spec, run_dir, None, [], popen=lambda c, **k: launched.append(c), executor=_executor([]), sampler=lambda: 8 * GIB, stats_sampler=lambda: [])
    assert no_docker["status"] == runner.STATUS_MISSING and not launched
