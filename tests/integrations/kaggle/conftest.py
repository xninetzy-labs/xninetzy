from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Sequence

import pytest

from xninetzy.core.config import get_settings
from xninetzy.integrations.kaggle import backend as backend_module
from xninetzy.integrations.kaggle.backend import KaggleBackendError, OpResult
from xninetzy.integrations.kaggle.services import datasets, kernels


class FakeBackend:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.statuses: dict[str, str] = {}
        self.failures: dict[str, str] = {}
        self.outputs: dict[str, Any] = {}
        self.pushes: list[dict[str, Any]] = []
        self.push_errors: list[str] = []
        self.push_raises: KaggleBackendError | None = None
        self.quota_remaining = 85_000
        self.username = "tester"
        self.datasets: dict[str, dict[str, Any]] = {}
        self.files: dict[str, list[dict[str, Any]]] = {}

    def run(
        self,
        operations: Sequence[tuple[str, dict[str, Any]]],
        *,
        bearer_token: str | None = None,
        timeout: int | None = None,
    ) -> list[OpResult]:
        results = []
        for name, args in operations:
            self.calls.append((name, args))
            results.append(getattr(self, "_" + name)(args))
        return results

    def names(self) -> list[str]:
        return [name for name, _ in self.calls]

    def _whoami(self, args: dict[str, Any]) -> OpResult:
        return OpResult(ok=True, data={"username": self.username})

    def _quota(self, args: dict[str, Any]) -> OpResult:
        return OpResult(
            ok=True,
            data={
                "gpu": {
                    "total_seconds": 108_000,
                    "used_seconds": 108_000 - self.quota_remaining,
                    "reserved_seconds": 0,
                    "remaining_seconds": self.quota_remaining,
                },
                "tpu": None,
                "refresh_time": None,
            },
        )

    def _dataset_list(self, args: dict[str, Any]) -> OpResult:
        rows = [{"ref": ref, **meta} for ref, meta in self.datasets.items() if args["query"].lower() in ref]
        return OpResult(ok=True, data={"datasets": rows[: args["limit"]]})

    def _dataset_get(self, args: dict[str, Any]) -> OpResult:
        meta = self.datasets.get(args["ref"])
        if meta is None:
            return OpResult(ok=False, error_type="HTTPError", error_message="403 Forbidden", status_code=403)
        return OpResult(ok=True, data={"ref": args["ref"], **meta})

    def _dataset_files(self, args: dict[str, Any]) -> OpResult:
        return OpResult(ok=True, data={"files": self.files.get(args["ref"], []), "has_more": False})

    def _dataset_download(self, args: dict[str, Any]) -> OpResult:
        target = Path(args["path"])
        target.mkdir(parents=True, exist_ok=True)
        (target / "data.csv").write_text("a,b\n1,2\n")
        return OpResult(ok=True, data={"path": str(target), "files": [{"name": "data.csv", "bytes": 8}]})

    def _kernel_push(self, args: dict[str, Any]) -> OpResult:
        if self.push_raises is not None:
            raise self.push_raises
        if self.push_errors:
            return OpResult(ok=True, data={"error": self.push_errors.pop(0), "invalid": {}, "url": None, "version": None})
        reference = args["metadata"]["id"]
        self.pushes.append(args)
        self.statuses[reference] = "QUEUED"
        return OpResult(ok=True, data={"error": None, "invalid": {}, "url": "https://kaggle.test/" + reference, "version": 1})

    def _kernel_status(self, args: dict[str, Any]) -> OpResult:
        reference = args["kernel"]
        if reference not in self.statuses:
            return OpResult(ok=False, error_type="HTTPError", error_message="404 Not Found", status_code=404)
        return OpResult(ok=True, data={"status": self.statuses[reference], "failure_message": self.failures.get(reference)})

    def _kernel_output(self, args: dict[str, Any]) -> OpResult:
        reference = args["kernel"]
        if reference not in self.statuses:
            return OpResult(ok=False, error_type="HTTPError", error_message="404 Not Found", status_code=404)
        reads: dict[str, Any] = {}
        for wanted in args.get("read") or []:
            payload = self.outputs.get(reference, {}).get(wanted)
            if payload is None:
                reads[wanted] = None
            elif isinstance(payload, str):
                reads[wanted] = {"text": payload, "truncated": False, "bytes": len(payload)}
            else:
                text = json.dumps(payload)
                reads[wanted] = {"text": text, "truncated": False, "bytes": len(text)}
        data: dict[str, Any] = {"files": sorted(self.outputs.get(reference, {})), "has_more": False, "next_page_token": None, "reads": reads}
        if args.get("log_tail_chars"):
            data["log_tail"] = "log line"
        return OpResult(ok=True, data=data)

    def _kernel_logs(self, args: dict[str, Any]) -> OpResult:
        return OpResult(ok=True, data={"log_tail": "live log"})

    def finish(self, reference: str, summary: Any = None, status: str = "COMPLETE") -> None:
        self.statuses[reference] = status
        if summary is not None:
            self.outputs.setdefault(reference, {})["summary.json"] = summary


@pytest.fixture
def kaggle_workspace(tmp_path, monkeypatch):
    workspace = tmp_path / "kaggle-workspace"
    workspace.mkdir()
    monkeypatch.setenv("KAGGLE_WORKSPACE_DIR", str(workspace))
    monkeypatch.setenv("KAGGLE_SOURCE_ROOTS", "")
    get_settings.cache_clear()
    kernels.reset_username_cache()
    datasets.reset_cache()
    yield workspace
    get_settings.cache_clear()


@pytest.fixture
def no_credentials(tmp_path, monkeypatch):
    empty = tmp_path / "empty-kaggle-config"
    empty.mkdir()
    monkeypatch.setenv("KAGGLE_CONFIG_DIR", str(empty))
    for name in ("KAGGLE_USERNAME", "KAGGLE_KEY", "KAGGLE_API_TOKEN"):
        monkeypatch.delenv(name, raising=False)
    return empty


@pytest.fixture
def credentials(tmp_path, monkeypatch):
    config = tmp_path / "kaggle-config"
    config.mkdir()
    (config / "access_token").write_text("not-a-real-token")
    monkeypatch.setenv("KAGGLE_CONFIG_DIR", str(config))
    for name in ("KAGGLE_USERNAME", "KAGGLE_KEY", "KAGGLE_API_TOKEN"):
        monkeypatch.delenv(name, raising=False)
    return config


@pytest.fixture
def fake_backend(kaggle_workspace, credentials):
    fake = FakeBackend()
    backend_module.set_backend(fake)
    yield fake
    backend_module.set_backend(None)


@pytest.fixture
def worker_file(kaggle_workspace):
    path = kaggle_workspace / "worker.py"
    path.write_text("print(JOB)\n")
    return path
