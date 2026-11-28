import json

from xninetzy.integrations.kaggle import services


def setup_pipeline():
    services.pipeline_plan(owner="test-owner", name="terminal-check", jobs=[
        {"slug": "terminal-job", "source_path": "worker.py", "summary_required": True},
    ])
    return services.pipeline_tick(owner="test-owner", name="terminal-check", idempotency_key="first")


def test_scheduler_marker_is_written_only_when_work_is_terminal(fake_backend, worker_file, kaggle_workspace):
    marker = kaggle_workspace / "pipelines/terminal-check.terminal.json"
    assert setup_pipeline().payload["done"] is False
    assert not marker.exists()
    fake_backend.finish("tester/terminal-job", {"complete": True})
    result = services.pipeline_tick(owner="test-owner", name="terminal-check", idempotency_key="second")
    assert result.payload["done"] is True
    assert json.loads(marker.read_text())["done"] is True


def test_scheduler_marker_stops_blocked_work_without_restarting_it(fake_backend, worker_file, kaggle_workspace):
    setup_pipeline()
    fake_backend.finish("tester/terminal-job", status="ERROR")
    result = services.pipeline_tick(owner="test-owner", name="terminal-check", idempotency_key="second")
    assert result.payload["blocked"] is True
    marker = kaggle_workspace / "pipelines/terminal-check.terminal.json"
    assert json.loads(marker.read_text())["blocked"] is True
    assert len(fake_backend.pushes) == 1
