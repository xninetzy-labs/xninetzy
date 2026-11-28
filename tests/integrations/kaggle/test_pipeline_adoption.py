from __future__ import annotations

import json

import pytest

from xninetzy.integrations.kaggle import services

OWNER = "test-owner"


def make_plan(**extra):
    return services.pipeline_plan(
        owner=OWNER, name="recovery", limits={"cpu": 1, "gpu": 0},
        jobs=[{"slug": "job-alpha", "source_path": "worker.py", **extra}],
    )


def test_adopt_running_kernel_without_resubmitting_it(fake_backend, worker_file):
    fake_backend.statuses["tester/old-running-job"] = "RUNNING"
    result = make_plan(adopt_run="old-running-job")
    assert result.status == "planned"
    assert result.payload["counts"] == {"submitted": 1}
    tick = services.pipeline_tick(owner=OWNER, name="recovery", idempotency_key="tick-1")
    assert tick.payload["submitted"] == []
    assert fake_backend.pushes == []


def test_adopt_complete_output_and_mount_its_actual_slug(fake_backend, worker_file):
    fake_backend.finish("tester/old-complete-job", {"complete": True})
    result = services.pipeline_plan(owner=OWNER, name="recovery", jobs=[
        {"slug": "job-alpha", "source_path": "worker.py", "adopt_run": "old-complete-job", "summary_required": True},
        {"slug": "job-beta", "source_path": "worker.py", "depends_on": ["job-alpha"]},
    ])
    assert result.status == "planned"
    assert result.payload["counts"] == {"complete": 1, "pending": 1}
    services.pipeline_tick(owner=OWNER, name="recovery", idempotency_key="tick-1")
    assert len(fake_backend.pushes) == 1
    assert fake_backend.pushes[0]["metadata"]["kernel_sources"] == ["tester/old-complete-job"]


@pytest.mark.parametrize("attempt", [3, 12])
def test_partial_adoption_continues_after_existing_attempt_number(fake_backend, worker_file, kaggle_workspace, attempt):
    previous = f"job-alpha-r{attempt}"
    following = f"job-alpha-r{attempt + 1}"
    fake_backend.finish("tester/" + previous, {"complete": False, "progress": 7})
    result = make_plan(adopt_run=previous, max_attempts=32, summary_required=True)
    assert result.status == "planned"
    state = json.loads((kaggle_workspace / "pipelines/recovery.json").read_text())
    assert state["jobs"][0]["run_slug"] == following
    assert state["jobs"][0]["previous_sources"] == [previous]
    services.pipeline_tick(owner=OWNER, name="recovery", idempotency_key="tick-1")
    assert fake_backend.pushes[0]["metadata"]["id"] == "tester/" + following
    assert fake_backend.pushes[0]["metadata"]["kernel_sources"] == ["tester/" + previous]


def test_missing_adopted_kernel_never_becomes_a_fresh_submission(fake_backend, worker_file, kaggle_workspace):
    result = make_plan(adopt_run="missing-old-job")
    assert result.status == "invalid_input"
    assert result.payload["error"]["error_code"] == "KAGGLE_ADOPTION_UNVERIFIED"
    assert not (kaggle_workspace / "pipelines/recovery.json").exists()
    assert fake_backend.pushes == []


def test_cancelled_adopted_kernel_remains_terminal(fake_backend, worker_file):
    fake_backend.finish("tester/cancelled-old-job", status="CANCEL_ACKNOWLEDGED")
    result = make_plan(adopt_run="cancelled-old-job", max_attempts=8)
    assert result.status == "planned"
    assert result.payload["counts"] == {"failed": 1}
    services.pipeline_tick(owner=OWNER, name="recovery", idempotency_key="tick-1")
    assert fake_backend.pushes == []


def test_adoption_rejects_a_different_account_reference(fake_backend, worker_file):
    result = make_plan(adopt_run="someone-else/private-job")
    assert result.status == "invalid_input"
    assert fake_backend.calls == []
