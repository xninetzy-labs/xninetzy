from __future__ import annotations

import importlib.util
import ast
import json
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.fixture
def controller(tmp_path, monkeypatch):
    path = Path(__file__).resolve().parents[3] / "scripts/kaggle_biodiversity/control.py"
    spec = importlib.util.spec_from_file_location("biodiversity_control", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "ROOT", tmp_path)
    (tmp_path / "remote_worker.py").write_text("raise SystemExit('Kaggle only')\n")
    return module


def test_generated_remote_job_is_private_and_has_only_declared_inputs(controller):
    folder = controller.build("test-job", {"mode": "extract"}, ["owner/raw-source"], gpu=True)
    metadata = json.loads((folder / "kernel-metadata.json").read_text())
    assert metadata["is_private"] is True
    assert metadata["enable_gpu"] is True
    assert metadata["kernel_sources"] == ["owner/raw-source"]
    source = (folder / metadata["code_file"]).read_text()
    config = ast.literal_eval(source.splitlines()[0].removeprefix("JOB = "))
    assert config["mode"] == "extract"
    assert config["worker_sha256"] == controller.worker_hash()
    assert "Kaggle only" in source


def test_kaggle_rejection_never_becomes_submission_receipt(controller, monkeypatch):
    result = SimpleNamespace(error="resource unavailable", invalid_kernel_sources=[], invalid_dataset_sources=[])
    monkeypatch.setattr(controller, "api", lambda: SimpleNamespace(kernels_push=lambda *a, **kw: result))
    with pytest.raises(RuntimeError, match="did not accept"):
        controller.push("test-job", {"mode": "extract"})


@pytest.mark.parametrize("name", ["report.pdf", "results.json", "texts/report.json.gz", "biodiversity_scores.xlsx"])
def test_controller_never_fetches_reports_or_extracted_data(controller, name):
    with pytest.raises(RuntimeError, match="execution status"):
        controller.read_status_json(SimpleNamespace(files=[]), name)


def test_incomplete_inventory_cannot_start_campaign(controller, monkeypatch):
    monkeypatch.setattr(controller, "output_response", lambda slug: None)
    monkeypatch.setattr(controller, "read_status_json", lambda response: {"complete": False})
    with pytest.raises(RuntimeError, match="verified complete"):
        controller.initialize_campaign("inventory")
    assert not (controller.ROOT / "campaign_state.json").exists()


def test_acknowledged_cancellation_is_terminal_and_never_replayed(controller, monkeypatch):
    job = {"slug": "cancelled-job", "mode": "extract", "state": "submitted", "gpu": True, "depends": []}
    controller.save_state({"jobs": [job], "smoke_verified_hash": controller.worker_hash(), "smoke_verified": True})
    response = SimpleNamespace(status=SimpleNamespace(name="CANCEL_ACKNOWLEDGED"), failure_message="")
    monkeypatch.setattr(controller, "api", lambda: SimpleNamespace(kernels_status=lambda slug: response))
    monkeypatch.setattr(controller, "push", lambda *a, **kw: pytest.fail("cancelled job was replayed"))
    controller.campaign_tick()
    state = json.loads((controller.ROOT / "campaign_state.json").read_text())
    assert state["jobs"][0]["state"] == "failed"
    assert state["jobs"][0]["remote_status"] == "CANCEL_ACKNOWLEDGED"


def test_bounded_live_log_timeout_closes_stream_without_transport_error(controller, monkeypatch):
    import signal
    from requests.exceptions import ConnectionError

    handlers, closed = [], []
    monkeypatch.setattr(signal, "signal", lambda signum, handler: handlers.append(handler))
    monkeypatch.setattr(signal, "alarm", lambda seconds: None)

    def wrapped_stream(slug):
        try:
            try:
                handlers[0]()
            except Exception as exc:
                raise ConnectionError("read timed out") from exc
            yield {"data": "unreachable"}
        finally:
            closed.append(True)

    monkeypatch.setattr(controller, "api", lambda: SimpleNamespace(kernels_logs_stream=wrapped_stream))
    controller.live_logs("test-job")
    assert closed == [True]
