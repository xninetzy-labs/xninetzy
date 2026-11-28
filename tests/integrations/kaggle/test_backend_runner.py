from __future__ import annotations

import json
import subprocess
import sys
import types
from contextlib import contextmanager
from datetime import timedelta
from types import SimpleNamespace

import pytest

from xninetzy.core.config import get_settings
from xninetzy.integrations.kaggle import backend as backend_module
from xninetzy.integrations.kaggle.backend import KaggleBackendError, SubprocessBackend
from xninetzy.integrations.kaggle.runner import sdk_runner


def completed(stdout: str, stderr: str = "", code: int = 0) -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(args=[], returncode=code, stdout=stdout, stderr=stderr)


def test_decode_ignores_noise_and_maps_results() -> None:
    stdout = "Warning: outdated\n" + json.dumps(
        {"results": [{"ok": True, "data": {"a": 1}}, {"ok": False, "error": {"type": "HTTPError", "message": "no", "status_code": 403}}]}
    ) + "\n"
    results = backend_module._decode([("x", {}), ("y", {})], completed(stdout))
    assert results[0].ok and results[0].data == {"a": 1}
    assert not results[1].ok and results[1].status_code == 403 and results[1].error_type == "HTTPError"


@pytest.mark.parametrize(
    "stdout",
    ["", "no json here\n", "{not json}\n", json.dumps({"results": []}) + "\n", json.dumps({"other": 1}) + "\n"],
)
def test_decode_rejects_protocol_violations(stdout) -> None:
    with pytest.raises(KaggleBackendError) as caught:
        backend_module._decode([("x", {})], completed(stdout, stderr="trace"))
    assert caught.value.code == "KAGGLE_RUNNER_PROTOCOL"


def test_subprocess_backend_builds_isolated_command_and_environment(monkeypatch, kaggle_workspace) -> None:
    seen = {}

    def fake_run(command, **kwargs):
        seen["command"], seen["kwargs"] = command, kwargs
        return completed(json.dumps({"results": [{"ok": True, "data": {}}]}))

    monkeypatch.setattr(backend_module, "resolve_python", lambda: "/opt/py/bin/python3")
    monkeypatch.setattr(backend_module.subprocess, "run", fake_run)
    monkeypatch.setenv("PYTHONPATH", "/should/not/leak")
    monkeypatch.setenv("KAGGLE_KEY", "keep-me")
    SubprocessBackend().run([("whoami", {})], bearer_token="tok-123", timeout=77)
    assert seen["command"][:3] == ["/opt/py/bin/python3", "-E", "-P"]
    assert seen["command"][3] == str(backend_module.RUNNER)
    environment = seen["kwargs"]["env"]
    assert not any(key.startswith("PYTHON") for key in environment)
    assert environment["KAGGLE_API_TOKEN"] == "tok-123"
    assert environment["KAGGLE_KEY"] == "keep-me"
    assert seen["kwargs"]["timeout"] == 77
    assert json.loads(seen["kwargs"]["input"]) == {"ops": [{"op": "whoami", "args": {}}]}
    assert seen["kwargs"]["cwd"] == str(kaggle_workspace.resolve())


def test_subprocess_backend_does_not_inject_token_when_absent(monkeypatch, kaggle_workspace) -> None:
    seen = {}

    def fake_run(command, **kwargs):
        seen.update(kwargs)
        return completed(json.dumps({"results": [{"ok": True, "data": {}}]}))

    monkeypatch.setattr(backend_module, "resolve_python", lambda: "py")
    monkeypatch.setattr(backend_module.subprocess, "run", fake_run)
    monkeypatch.delenv("KAGGLE_API_TOKEN", raising=False)
    SubprocessBackend().run([("whoami", {})])
    assert "KAGGLE_API_TOKEN" not in seen["env"]


def test_subprocess_timeout_becomes_reconcile_error(monkeypatch, kaggle_workspace) -> None:
    def fake_run(command, **kwargs):
        raise subprocess.TimeoutExpired(command, kwargs["timeout"])

    monkeypatch.setattr(backend_module, "resolve_python", lambda: "py")
    monkeypatch.setattr(backend_module.subprocess, "run", fake_run)
    with pytest.raises(KaggleBackendError) as caught:
        SubprocessBackend().run([("kernel_push", {})], timeout=30)
    assert caught.value.code == "KAGGLE_RUNNER_TIMEOUT"
    assert "reconcile" in caught.value.message


def test_unstartable_interpreter_is_reported_as_unavailable(monkeypatch, kaggle_workspace) -> None:
    def fake_run(command, **kwargs):
        raise FileNotFoundError("nope")

    monkeypatch.setattr(backend_module, "resolve_python", lambda: "missing-python")
    monkeypatch.setattr(backend_module.subprocess, "run", fake_run)
    with pytest.raises(KaggleBackendError) as caught:
        SubprocessBackend().run([("whoami", {})])
    assert caught.value.code == "KAGGLE_RUNNER_UNAVAILABLE"


def test_resolve_python_prefers_configured_interpreter(monkeypatch) -> None:
    monkeypatch.setenv("KAGGLE_PYTHON", "/configured/python")
    get_settings.cache_clear()
    monkeypatch.setattr(backend_module, "_supports_sdk", lambda candidate: candidate == "/configured/python")
    try:
        assert backend_module.resolve_python() == "/configured/python"
    finally:
        get_settings.cache_clear()


def test_resolve_python_reports_missing_sdk_with_remedy(monkeypatch) -> None:
    monkeypatch.setenv("KAGGLE_PYTHON", "")
    get_settings.cache_clear()
    monkeypatch.setattr(backend_module, "_supports_sdk", lambda candidate: False)
    try:
        with pytest.raises(KaggleBackendError) as caught:
            backend_module.resolve_python()
    finally:
        get_settings.cache_clear()
    assert caught.value.code == "KAGGLE_SDK_MISSING"
    assert "KAGGLE_PYTHON" in caught.value.message
    assert caught.value.to_dict()["retryable"] is False


def test_runner_protocol_works_as_a_real_subprocess_without_the_sdk() -> None:
    completed_process = subprocess.run(
        [sys.executable, "-E", "-P", str(backend_module.RUNNER)],
        input=json.dumps({"ops": [{"op": "bogus", "args": {}}]}),
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    results = backend_module._decode([("bogus", {})], completed_process)
    assert results[0].ok is False
    assert "unknown operation" in results[0].error_message


class FakeApi:
    def __init__(self) -> None:
        self.pushed: dict = {}

    def get_config_value(self, name):
        return "tester" if name == "username" else None

    def kernels_status(self, reference):
        return SimpleNamespace(status=SimpleNamespace(name="running"), failure_message="")

    def dataset_list(self, search=None, page=1):
        pages = {1: [SimpleNamespace(ref="a/one", title="One", total_bytes=1, last_updated=None)], 2: [SimpleNamespace(ref="a/two", title="Two", total_bytes=2, last_updated=None)]}
        return pages.get(page, [])

    def dataset_list_files(self, reference, page_token=None, page_size=20):
        files = [SimpleNamespace(name="a.csv", total_bytes=10), SimpleNamespace(name="b.csv", total_bytes=20)]
        if page_token is None:
            return SimpleNamespace(files=files[:1], next_page_token="more")
        return SimpleNamespace(files=files[1:], next_page_token="")

    def kernels_push(self, folder, timeout=None, acc=None):
        from pathlib import Path

        root = Path(folder)
        self.pushed = {
            "files": sorted(path.name for path in root.iterdir()),
            "metadata": json.loads((root / "kernel-metadata.json").read_text()),
            "code": (root / "worker.py").read_text(),
            "timeout": timeout,
            "acc": acc,
        }
        return SimpleNamespace(error="", invalid_kernel_sources=[], invalid_dataset_sources=["x/y"], url="https://k/u", version_number=2)

    def dataset_download_files(self, reference, path=None, force=False, quiet=True, unzip=False):
        from pathlib import Path

        (Path(path) / "nested").mkdir(parents=True, exist_ok=True)
        (Path(path) / "nested" / "f.csv").write_text("x")


def run_ops(operations, api=None):
    return sdk_runner.execute({"ops": [{"op": name, "args": args} for name, args in operations]}, api_factory=lambda: api or FakeApi())["results"]


def test_runner_whoami_and_status_normalization() -> None:
    results = run_ops([("whoami", {}), ("kernel_status", {"kernel": "tester/job"})])
    assert results[0] == {"ok": True, "data": {"username": "tester"}}
    assert results[1]["data"] == {"status": "RUNNING", "failure_message": None}


def test_owned_presence_paginates_and_checks_private_witness():
    class OwnedApi(FakeApi):
        def kernels_list(self, **kwargs):
            assert kwargs["mine"] is True and kwargs["page_size"] == 100
            if kwargs["page"] == 1:
                return [SimpleNamespace(ref=f"tester/job-{i}", is_private=True) for i in range(100)]
            return [SimpleNamespace(ref="tester/witness", is_private=True)]

    result = run_ops([("kernel_presence", {"kernels": ["tester/job-99", "tester/absent"],
                                           "witness": "tester/witness"})], OwnedApi())[0]
    assert result["ok"]
    assert result["data"] == {"username": "tester", "complete": True, "witness_present": True,
                              "found": ["tester/job-99"], "scanned": 101, "redacted": 0}


def test_owned_presence_counts_private_notebooks_that_kaggle_masks():
    masked = SimpleNamespace(ref="", id=0, title="[Private Notebook]")
    api = FakeApi()
    api.kernels_list = lambda **kwargs: [masked, SimpleNamespace(ref="tester/witness"), masked]
    result = run_ops([("kernel_presence", {"kernels": ["tester/absent"], "witness": "tester/witness"})], api)[0]
    assert result["ok"]
    assert result["data"]["redacted"] == 2
    assert result["data"]["scanned"] == 1
    assert result["data"]["found"] == []


@pytest.mark.parametrize("rows", [None, [SimpleNamespace(ref="foreign/job")], [SimpleNamespace(ref=None)],
                                  [SimpleNamespace(ref="", id=7, title="[Private Notebook]")],
                                  [SimpleNamespace(ref="", id=0, title="Untitled")]])
def test_invalid_owned_listing_is_never_absence_proof(rows):
    api = FakeApi()
    api.kernels_list = lambda **kwargs: rows
    result = run_ops([("kernel_presence", {"kernels": ["tester/absent"], "witness": "tester/witness"})], api)[0]
    assert result["ok"] is False


def test_owned_presence_page_cap_is_incomplete():
    api = FakeApi()
    api.kernels_list = lambda **kwargs: [SimpleNamespace(ref=f"tester/job-{kwargs['page']}-{i}") for i in range(100)]
    result = run_ops([("kernel_presence", {"kernels": ["tester/absent"], "witness": "tester/job-1-0"})], api)[0]
    assert result["data"]["complete"] is False
    assert result["data"]["scanned"] == 2500


def test_runner_dataset_list_paginates_until_limit() -> None:
    results = run_ops([("dataset_list", {"query": "x", "limit": 2})])
    assert [row["ref"] for row in results[0]["data"]["datasets"]] == ["a/one", "a/two"]


def test_runner_dataset_files_follows_page_tokens() -> None:
    results = run_ops([("dataset_files", {"ref": "a/b", "limit": 5})])
    assert [f["name"] for f in results[0]["data"]["files"]] == ["a.csv", "b.csv"]
    assert results[0]["data"]["has_more"] is False


def test_runner_push_writes_worker_and_metadata_and_reports_invalid_sources() -> None:
    api = FakeApi()
    arguments = {"code": "print(1)\n", "code_file": "worker.py", "metadata": {"id": "tester/job"}, "timeout": "300", "accelerator": "NvidiaTeslaT4"}
    results = run_ops([("kernel_push", arguments)], api)
    assert api.pushed["files"] == ["kernel-metadata.json", "worker.py"]
    assert api.pushed["metadata"] == {"id": "tester/job"}
    assert api.pushed["acc"] == "NvidiaTeslaT4"
    data = results[0]["data"]
    assert data["error"] is None
    assert data["invalid"] == {"invalid_dataset_sources": ["x/y"]}
    assert data["version"] == 2


def test_runner_download_lists_nested_files(tmp_path) -> None:
    results = run_ops([("dataset_download", {"ref": "a/b", "path": str(tmp_path / "out")})])
    assert results[0]["data"]["files"] == [{"name": "nested/f.csv", "bytes": 1}]


def test_runner_maps_http_status_and_isolates_failures() -> None:
    class Broken(FakeApi):
        def kernels_status(self, reference):
            error = RuntimeError("403 Client Error")
            error.response = SimpleNamespace(status_code=403)
            raise error

    results = run_ops([("kernel_status", {"kernel": "a/b"}), ("whoami", {})], Broken())
    assert results[0]["ok"] is False and results[0]["error"]["status_code"] == 403
    assert results[1]["ok"] is True


def test_runner_reuses_authentication_failure_and_catches_system_exit() -> None:
    calls = []

    def factory():
        calls.append(1)
        raise SystemExit("could not find credentials")

    results = sdk_runner.execute({"ops": [{"op": "whoami"}, {"op": "quota"}]}, api_factory=factory)["results"]
    assert len(calls) == 1
    assert all(item["ok"] is False for item in results)
    assert results[0] == results[1]


def test_runner_quota_computes_remaining_seconds() -> None:
    item = SimpleNamespace(total_time_allowed=timedelta(hours=30), time_used=timedelta(hours=6), time_reserved=timedelta(hours=1))
    quota = sdk_runner._quota(item)
    assert quota["remaining_seconds"] == 23 * 3600
    assert sdk_runner._quota(None) is None
    assert sdk_runner._quota(SimpleNamespace(total_time_allowed=None, time_used=None, time_reserved=None))["remaining_seconds"] is None


def test_runner_plain_log_flattens_kaggle_event_json() -> None:
    raw = json.dumps([{"stream_name": "stdout", "data": "one\n"}, {"stream_name": "stderr", "data": "two\n"}])
    assert sdk_runner._plain_log(raw) == "one\ntwo\n"
    assert sdk_runner._plain_log("plain text") == "plain text"
    assert sdk_runner._plain_log(None) == ""


def test_runner_repairs_double_encoded_progress_glyphs_only_when_safe() -> None:
    garbled = "\u00e2\u0096\u0088\u00e2\u0096\u0088 done"
    assert sdk_runner._repair(garbled) == "\u2588\u2588 done"
    assert sdk_runner._repair("plain ascii") == "plain ascii"
    assert sdk_runner._repair("caf\u00e9 stays") == "caf\u00e9 stays"


def test_runner_kernel_output_reads_named_files_with_bounds(monkeypatch) -> None:
    class Request:
        pass

    module = types.ModuleType("kagglesdk.kernels.types.kernels_api_service")
    module.ApiListKernelSessionOutputRequest = Request
    for name in ("kagglesdk", "kagglesdk.kernels", "kagglesdk.kernels.types"):
        monkeypatch.setitem(sys.modules, name, types.ModuleType(name))
    monkeypatch.setitem(sys.modules, "kagglesdk.kernels.types.kernels_api_service", module)
    captured = {}

    class Client:
        def list_kernel_session_output(self, request):
            captured["request"] = request
            files = [SimpleNamespace(file_name="out/summary.json", url="u1"), SimpleNamespace(file_name="big.bin", url="u2")]
            return SimpleNamespace(files=files, log=json.dumps([{"data": "hello log"}]), next_page_token="")

    class Api(FakeApi):
        @contextmanager
        def build_kaggle_client(self):
            yield SimpleNamespace(kernels=SimpleNamespace(kernels_api_client=Client()))

    monkeypatch.setattr(sdk_runner, "_read_remote", lambda url, limit: {"text": f"{url}:{limit}", "truncated": False, "bytes": 3})
    arguments = {"kernel": "tester/job", "read": ["summary.json", "absent.json"], "max_read_bytes": 500, "log_tail_chars": 5}
    data = run_ops([("kernel_output", arguments)], Api())[0]["data"]
    assert captured["request"].user_name == "tester" and captured["request"].kernel_slug == "job"
    assert data["files"] == ["out/summary.json", "big.bin"]
    assert data["reads"]["summary.json"]["text"] == "u1:500"
    assert data["reads"]["absent.json"] is None
    assert data["log_tail"] == "o log"
