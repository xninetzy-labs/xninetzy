from __future__ import annotations

import json
import time

import pytest

from xninetzy.integrations.kaggle import services as kaggle_services
from xninetzy.integrations.kaggle.backend import KaggleBackendError

OWNER = "test-owner"


def job(slug: str, **extra):
    return {"slug": slug, "source_path": "worker.py", **extra}


def plan(name: str = "demo", jobs=None, **kwargs):
    return kaggle_services.pipeline_plan(
        owner=OWNER, name=name, jobs=jobs if jobs is not None else [job("job-alpha")], **kwargs
    )


def tick(name: str = "demo", key: str = "tick-1"):
    return kaggle_services.pipeline_tick(owner=OWNER, name=name, idempotency_key=key)


def state_of(result, slug: str) -> str:
    return next(item["state"] for item in result.payload["jobs"] if item["slug"] == slug)


def test_plan_saves_normalized_state_without_touching_kaggle(fake_backend, worker_file) -> None:
    result = plan(jobs=[job("job-alpha"), job("job-beta", depends_on=["job-alpha"])])
    assert result.status == "planned"
    assert result.payload["counts"] == {"pending": 2}
    assert result.payload["limits"] == {"cpu": 4, "gpu": 1}
    assert fake_backend.calls == []


def test_plan_materializes_inline_source_inside_workspace(fake_backend, kaggle_workspace) -> None:
    result = plan(jobs=[{"slug": "inline-job", "source": "print(JOB)\n"}])
    assert result.status == "planned"
    stored = json.loads((kaggle_workspace / "pipelines" / "demo.json").read_text())
    path = stored["jobs"][0]["source_path"]
    assert path.startswith(str(kaggle_workspace.resolve()))
    assert open(path).read() == "print(JOB)\n"


@pytest.mark.parametrize(
    "jobs, fragment",
    [
        ([job("job-alpha"), job("job-alpha")], "unique"),
        ([job("job-alpha", depends_on=["ghost-job"])], "invalid dependencies"),
        ([job("job-alpha", depends_on=["job-alpha"])], "invalid dependencies"),
        (
            [job("job-alpha", depends_on=["job-beta"]), job("job-beta", depends_on=["job-alpha"])],
            "cycle",
        ),
        ([job("job-alpha", surprise=1)], "unknown job keys"),
        ([job("job-alpha", accelerator="tpu")], "accelerator"),
        ([job("job-alpha", time_budget_seconds=5)], "time_budget_seconds"),
        ([job("job-alpha", max_attempts=0)], "max_attempts"),
        ([{"slug": "job-alpha"}], "exactly one of source"),
        ([job("x" * 46)], "characters"),
        ([job("job-alpha", dataset_sources=["bad ref"])], "dataset source"),
        ([job("job-alpha", params={"x": object()})], "JSON-serializable"),
        ([], "1-200"),
    ],
)
def test_plan_rejects_invalid_specs(fake_backend, worker_file, jobs, fragment) -> None:
    result = plan(jobs=jobs)
    assert result.status == "invalid_input"
    assert fragment in result.payload["error"]["message"]


def test_plan_rejects_bad_name_and_limits(fake_backend, worker_file) -> None:
    assert plan(name="Bad Name").status == "invalid_input"
    assert plan(limits={"cpu": 99}).status == "invalid_input"
    assert plan(limits={"gpu": -1}).status == "invalid_input"


def test_plan_requires_source_inside_allowed_roots(fake_backend, tmp_path, kaggle_workspace) -> None:
    outside = tmp_path / "outside.py"
    outside.write_text("print(1)\n")
    result = plan(jobs=[{"slug": "job-alpha", "source_path": str(outside)}])
    assert result.status == "invalid_input"
    assert result.payload["error"]["error_code"] == "KAGGLE_SOURCE_OUTSIDE_ROOTS"


def test_replanning_identical_spec_is_unchanged_and_changed_spec_needs_replace(fake_backend, worker_file) -> None:
    plan()
    assert plan().status == "unchanged"
    blocked = plan(jobs=[job("job-alpha", params={"n": 2})])
    assert blocked.payload["error"]["error_code"] == "KAGGLE_PIPELINE_EXISTS"
    replaced = plan(jobs=[job("job-alpha", params={"n": 2})], replace=True)
    assert replaced.status == "planned"


def test_started_pipeline_cannot_be_replaced(fake_backend, worker_file) -> None:
    plan()
    tick()
    result = plan(jobs=[job("job-alpha", params={"n": 2})], replace=True)
    assert result.payload["error"]["error_code"] == "KAGGLE_PIPELINE_ACTIVE"


def test_tick_submits_only_jobs_whose_dependencies_are_complete(fake_backend, worker_file) -> None:
    plan(jobs=[job("job-alpha"), job("job-beta", depends_on=["job-alpha"])])
    first = tick()
    assert first.payload["submitted"] == ["job-alpha"]
    assert state_of(first, "job-alpha") == "submitted"
    assert state_of(first, "job-beta") == "pending"
    assert first.payload["next_tick_seconds"] == 60


def test_tick_advances_dependents_and_mounts_upstream_outputs(fake_backend, worker_file) -> None:
    plan(jobs=[job("job-alpha"), job("job-beta", depends_on=["job-alpha"])])
    tick(key="t1")
    fake_backend.finish("tester/job-alpha", {"complete": True})
    second = tick(key="t2")
    assert state_of(second, "job-alpha") == "complete"
    assert second.payload["submitted"] == ["job-beta"]
    beta = next(p for p in fake_backend.pushes if p["metadata"]["id"] == "tester/job-beta")
    assert beta["metadata"]["kernel_sources"] == ["tester/job-alpha"]
    fake_backend.finish("tester/job-beta", {"complete": True})
    third = tick(key="t3")
    assert third.payload["done"] is True
    assert third.payload["next_tick_seconds"] is None


def test_tick_respects_cpu_concurrency_limit(fake_backend, worker_file) -> None:
    plan(jobs=[job(f"job-{index}x") for index in range(5)], limits={"cpu": 2, "gpu": 0})
    first = tick(key="t1")
    assert len(first.payload["submitted"]) == 2
    fake_backend.finish("tester/job-0x", {"complete": True})
    second = tick(key="t2")
    assert second.payload["finished"] == ["job-0x"]
    assert len(second.payload["submitted"]) == 1


def test_same_tick_key_replays_stored_result_without_remote_calls(fake_backend, worker_file) -> None:
    plan()
    first = tick(key="same")
    calls = len(fake_backend.calls)
    again = tick(key="same")
    assert again.payload["replayed"] is True
    assert again.payload["submitted"] == first.payload["submitted"]
    assert len(fake_backend.calls) == calls


def test_failed_remote_status_marks_job_failed_and_blocks_dependents(fake_backend, worker_file) -> None:
    plan(jobs=[job("job-alpha"), job("job-beta", depends_on=["job-alpha"])])
    tick(key="t1")
    fake_backend.failures["tester/job-alpha"] = "boom"
    fake_backend.finish("tester/job-alpha", status="ERROR")
    result = tick(key="t2")
    assert state_of(result, "job-alpha") == "failed"
    assert state_of(result, "job-beta") == "pending"
    assert result.payload["blocked"] is True
    assert result.payload["needs_attention"][0]["failure"] == "boom"
    assert len(fake_backend.pushes) == 1


def test_cancelled_kernel_is_terminal_and_never_restarted(fake_backend, worker_file) -> None:
    plan()
    tick(key="t1")
    fake_backend.finish("tester/job-alpha", status="CANCEL_ACKNOWLEDGED")
    tick(key="t2")
    again = tick(key="t3")
    assert state_of(again, "job-alpha") == "failed"
    assert len(fake_backend.pushes) == 1


def test_incomplete_summary_creates_continuation_run_with_previous_output(fake_backend, worker_file) -> None:
    plan(jobs=[job("job-alpha", max_attempts=3, summary_required=True)])
    tick(key="t1")
    fake_backend.finish("tester/job-alpha", {"complete": False, "progress": 10})
    second = tick(key="t2")
    assert second.payload["submitted"] == ["job-alpha-r2"]
    assert next(j for j in second.payload["jobs"] if j["slug"] == "job-alpha")["attempt"] == 2
    continuation = fake_backend.pushes[-1]
    assert continuation["metadata"]["id"] == "tester/job-alpha-r2"
    assert continuation["metadata"]["kernel_sources"] == ["tester/job-alpha"]
    assert "'_attempt': 2" in continuation["code"].splitlines()[0]


def test_stalled_continuations_stop_as_partial(fake_backend, worker_file) -> None:
    plan(jobs=[job("job-alpha", max_attempts=10, summary_required=True)])
    tick(key="t0")
    reference = "tester/job-alpha"
    states = []
    for index in range(1, 6):
        fake_backend.finish(reference, {"complete": False, "progress": 5})
        result = tick(key=f"t{index}")
        states.append(state_of(result, "job-alpha"))
        reference = "tester/" + next(j for j in result.payload["jobs"] if j["slug"] == "job-alpha")["run_slug"]
        if states[-1] == "partial":
            break
    assert states[-1] == "partial"
    assert result.payload["needs_attention"][0]["state"] == "partial"
    assert result.payload["blocked"] is True


def test_attempt_cap_ends_in_partial(fake_backend, worker_file) -> None:
    plan(jobs=[job("job-alpha", max_attempts=1, summary_required=True)])
    tick(key="t1")
    fake_backend.finish("tester/job-alpha", {"complete": False, "progress": 1})
    result = tick(key="t2")
    assert state_of(result, "job-alpha") == "partial"
    assert len(fake_backend.pushes) == 1


def test_missing_summary_is_partial_only_when_required(fake_backend, worker_file) -> None:
    plan(name="strict", jobs=[job("job-strict", summary_required=True)])
    plan(name="loose", jobs=[job("job-loose")])
    tick(name="strict", key="s1")
    tick(name="loose", key="l1")
    fake_backend.finish("tester/job-strict")
    fake_backend.finish("tester/job-loose")
    assert state_of(tick(name="strict", key="s2"), "job-strict") == "partial"
    assert state_of(tick(name="loose", key="l2"), "job-loose") == "complete"


def test_summary_without_complete_flag_counts_as_complete_when_not_required(fake_backend, worker_file) -> None:
    plan()
    tick(key="t1")
    fake_backend.finish("tester/job-alpha", {"rows": 12})
    result = tick(key="t2")
    assert state_of(result, "job-alpha") == "complete"
    assert next(j for j in result.payload["jobs"] if j["slug"] == "job-alpha")["summary"] == {"rows": 12}


def test_deferred_summary_delays_the_continuation(fake_backend, worker_file) -> None:
    plan(jobs=[job("job-alpha", max_attempts=3, summary_required=True)])
    tick(key="t1")
    fake_backend.finish("tester/job-alpha", {"complete": False, "progress": 1, "deferred": {"retry_after_seconds": 1800}})
    result = tick(key="t2")
    assert state_of(result, "job-alpha") == "pending"
    assert result.payload["submitted"] == []
    assert result.payload["next_tick_seconds"] >= 60
    assert len(fake_backend.pushes) == 1


def defer_once(fake_backend, path, reference, retry_after=100):
    fake_backend.finish(reference, {"complete": False, "progress": 5, "deferred": {"retry_after_seconds": retry_after}})
    before = time.time()
    return before, tick(key=f"defer-{reference}")


def test_repeated_quota_deferrals_back_off_without_stalling(fake_backend, worker_file, kaggle_workspace) -> None:
    plan(jobs=[job("job-alpha", max_attempts=8, summary_required=True)])
    path = kaggle_workspace / "pipelines" / "demo.json"
    tick(key="t0")
    reference = "tester/job-alpha"
    delays = []
    for index in range(5):
        before, result = defer_once(fake_backend, path, reference)
        assert state_of(result, "job-alpha") == "pending"
        state = json.loads(path.read_text())
        delays.append(state["jobs"][0]["not_before"] - before)
        reference = "tester/" + state["jobs"][0]["run_slug"]
        state["jobs"][0]["not_before"] = 0
        path.write_text(json.dumps(state))
        tick(key=f"push-{index}")
    assert [round(value / 100) for value in delays] == [1, 1, 2, 4, 8]
    assert json.loads(path.read_text())["jobs"][0]["stalled"] == 0


def test_quota_backoff_is_capped(fake_backend, worker_file, kaggle_workspace) -> None:
    plan(jobs=[job("job-alpha", max_attempts=8, summary_required=True)])
    path = kaggle_workspace / "pipelines" / "demo.json"
    tick(key="t0")
    state = json.loads(path.read_text())
    state["jobs"][0].update(deferrals=50, last_progress=5.0)
    path.write_text(json.dumps(state))
    before, _ = defer_once(fake_backend, path, "tester/job-alpha")
    wait = json.loads(path.read_text())["jobs"][0]["not_before"] - before
    assert round(wait / 100) == 12


def test_progress_resets_the_quota_backoff(fake_backend, worker_file, kaggle_workspace) -> None:
    plan(jobs=[job("job-alpha", max_attempts=8, summary_required=True)])
    path = kaggle_workspace / "pipelines" / "demo.json"
    tick(key="t0")
    state = json.loads(path.read_text())
    state["jobs"][0].update(deferrals=6, last_progress=2.0)
    path.write_text(json.dumps(state))
    before, _ = defer_once(fake_backend, path, "tester/job-alpha")
    job_state = json.loads(path.read_text())["jobs"][0]
    assert job_state["deferrals"] == 0
    assert round((job_state["not_before"] - before) / 100) == 1


def test_gpu_job_waits_without_quota_and_gpu_or_cpu_falls_back(fake_backend, worker_file) -> None:
    fake_backend.quota_remaining = 100
    plan(jobs=[job("gpu-only", accelerator="gpu"), job("gpu-flex", accelerator="gpu_or_cpu")])
    result = tick()
    assert result.payload["submitted"] == ["gpu-flex"]
    assert state_of(result, "gpu-only") == "pending"
    pushed = fake_backend.pushes[0]
    assert pushed["metadata"]["enable_gpu"] is False


def test_gpu_job_uses_gpu_when_quota_available_and_caps_budget(fake_backend, worker_file) -> None:
    fake_backend.quota_remaining = 2_000
    plan(jobs=[job("gpu-only", accelerator="gpu", time_budget_seconds=36_000)])
    result = tick()
    assert result.payload["submitted"] == ["gpu-only"]
    pushed = fake_backend.pushes[0]
    assert pushed["metadata"]["enable_gpu"] is True
    assert pushed["accelerator"] == "NvidiaTeslaT4"
    assert "'time_budget_seconds': 1700" in pushed["code"].splitlines()[0]


def test_gpu_concurrency_limit_is_enforced(fake_backend, worker_file) -> None:
    plan(jobs=[job("gpu-one", accelerator="gpu"), job("gpu-two", accelerator="gpu")], limits={"cpu": 4, "gpu": 1})
    result = tick()
    assert result.payload["submitted"] == ["gpu-one"]


def test_transient_rejection_keeps_job_pending_and_backs_off(fake_backend, worker_file) -> None:
    fake_backend.push_errors = ["Maximum batch CPU session count reached"]
    plan(jobs=[job("job-alpha"), job("job-beta")])
    first = tick(key="t1")
    assert first.payload["submitted"] == []
    assert state_of(first, "job-alpha") == "pending"
    second = tick(key="t2")
    assert second.payload["submitted"] == []
    assert len(fake_backend.pushes) == 0


def test_permanent_rejection_fails_the_job(fake_backend, worker_file) -> None:
    fake_backend.push_errors = ["Invalid dataset source"]
    plan()
    result = tick()
    assert state_of(result, "job-alpha") == "failed"
    assert "Invalid dataset source" in result.payload["needs_attention"][0]["failure"]


def test_unknown_delivery_is_surfaced_and_never_replayed(fake_backend, worker_file) -> None:
    fake_backend.push_raises = KaggleBackendError("KAGGLE_RUNNER_TIMEOUT", "timed out")
    plan()
    first = tick(key="t1")
    assert state_of(first, "job-alpha") == "unknown_delivery"
    fake_backend.push_raises = None
    second = tick(key="t2")
    assert state_of(second, "job-alpha") == "unknown_delivery"
    assert fake_backend.pushes == []
    assert second.payload["blocked"] is True


def test_submitting_job_with_missing_kernel_becomes_unknown_after_grace(fake_backend, worker_file, kaggle_workspace) -> None:
    plan()
    path = kaggle_workspace / "pipelines" / "demo.json"
    state = json.loads(path.read_text())
    state["kaggle_user"] = "tester"
    state["jobs"][0]["state"] = "submitting"
    state["jobs"][0]["submitting_at"] = time.time() - 600
    path.write_text(json.dumps(state))
    result = tick()
    assert state_of(result, "job-alpha") == "unknown_delivery"
    assert fake_backend.pushes == []


def test_submitting_job_with_existing_kernel_is_promoted_to_submitted(fake_backend, worker_file, kaggle_workspace) -> None:
    plan()
    path = kaggle_workspace / "pipelines" / "demo.json"
    state = json.loads(path.read_text())
    state["kaggle_user"] = "tester"
    state["jobs"][0]["state"] = "submitting"
    state["jobs"][0]["submitting_at"] = time.time()
    path.write_text(json.dumps(state))
    fake_backend.statuses["tester/job-alpha"] = "RUNNING"
    result = tick()
    assert state_of(result, "job-alpha") == "submitted"
    assert fake_backend.pushes == []


def test_backend_outage_during_tick_returns_error_and_preserves_state(fake_backend, worker_file) -> None:
    plan()
    tick(key="t1")

    def explode(*args, **kwargs):
        raise KaggleBackendError("KAGGLE_RUNNER_TIMEOUT", "timed out")

    fake_backend.run = explode
    result = tick(key="t2")
    assert result.status == "error"
    status = kaggle_services.pipeline_status(owner=OWNER, name="demo")
    assert next(j for j in status.payload["jobs"] if j["slug"] == "job-alpha")["state"] == "submitted"


def test_status_lists_pipelines_and_reports_one(fake_backend, worker_file) -> None:
    plan(name="demo")
    plan(name="other", jobs=[job("job-gamma")])
    listing = kaggle_services.pipeline_status(owner=OWNER)
    assert sorted(item["pipeline"] for item in listing.payload["pipelines"]) == ["demo", "other"]
    single = kaggle_services.pipeline_status(owner=OWNER, name="demo")
    assert single.payload["counts"] == {"pending": 1}
    assert kaggle_services.pipeline_status(owner=OWNER, name="ghost-one").status == "not_found"


def test_tick_unknown_pipeline_and_missing_key(fake_backend, worker_file) -> None:
    assert tick(name="ghost-one").status == "not_found"
    plan()
    assert tick(key="").status == "invalid_input"


def test_tick_requires_authentication(no_credentials, kaggle_workspace) -> None:
    assert tick().status == "auth_required"


def test_pushes_inside_a_pipeline_are_ledger_protected(fake_backend, worker_file, kaggle_workspace) -> None:
    plan()
    tick(key="t1")
    ledger = json.loads((kaggle_workspace / "ledger" / "pushes.json").read_text())
    assert "pipeline:demo:job-alpha" in ledger
    assert ledger["pipeline:demo:job-alpha"]["state"] == "submitted"
