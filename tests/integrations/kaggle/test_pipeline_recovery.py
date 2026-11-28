import json
import time

import pytest

from xninetzy.integrations.kaggle import services
from xninetzy.integrations.kaggle.backend import OpResult
from xninetzy.integrations.kaggle.workspace import sha256_text

OWNER = "test-owner"


@pytest.fixture
def recovery(fake_backend, worker_file, kaggle_workspace, monkeypatch):
    fake_backend.finish("tester/witness-job", {"complete": True})
    services.pipeline_plan(owner=OWNER, name="repair", limits={"cpu": 1, "gpu": 0}, jobs=[
        {"slug": "witness-job", "source_path": "worker.py", "adopt_run": "witness-job"},
        {"slug": "affected-job", "source_path": "worker.py", "max_attempts": 8, "summary_required": True},
    ])
    path = kaggle_workspace / "pipelines/repair.json"
    state = json.loads(path.read_text())
    job = state["jobs"][1]
    job.update(state="unknown_delivery", run_slug="affected-job-r2", attempt=2,
               submitting_at=time.time()-3600, previous_sources=["old-checkpoint"])
    path.write_text(json.dumps(state))
    fake_backend.finish("tester/old-checkpoint", {"complete": False, "progress": 7})

    def presence(args):
        return OpResult(ok=True, data={
            "username": "tester", "complete": True, "witness_present": True,
            "found": [ref for ref in args["kernels"] if ref in fake_backend.statuses],
        })

    monkeypatch.setattr(fake_backend, "_kernel_presence", presence, raising=False)
    return fake_backend, path


def repair(**kwargs):
    return services.pipeline_tick(owner=OWNER, name="repair", idempotency_key="repair-1", **kwargs)


def test_existing_uncertain_run_is_adopted_without_replay(recovery):
    backend, path = recovery
    backend.statuses["tester/affected-job-r2"] = "RUNNING"
    result = repair(reconcile_jobs=["affected-job"])
    assert result.status == "ok"
    state = json.loads(path.read_text())
    assert state["jobs"][1]["state"] == "submitted"
    assert state["jobs"][1]["run_slug"] == "affected-job-r2"
    assert backend.pushes == []


def test_verified_absence_creates_new_attempt_with_saved_checkpoint(recovery):
    backend, path = recovery
    result = repair(reconcile_jobs=["affected-job"])
    assert result.status == "ok"
    job = json.loads(path.read_text())["jobs"][1]
    assert job["run_slug"] == "affected-job-r3"
    assert backend.pushes[0]["metadata"]["id"] == "tester/affected-job-r3"
    assert backend.pushes[0]["metadata"]["kernel_sources"] == ["tester/old-checkpoint"]


def test_incomplete_account_listing_never_authorizes_a_retry(recovery, monkeypatch):
    backend, path = recovery
    monkeypatch.setattr(backend, "_kernel_presence", lambda args: OpResult(ok=True, data={
        "username": "tester", "complete": False, "witness_present": True, "found": [],
    }))
    repair(reconcile_jobs=["affected-job"])
    assert json.loads(path.read_text())["jobs"][1]["state"] == "unknown_delivery"
    assert backend.pushes == []


def test_network_failure_is_not_treated_as_non_delivery(recovery, monkeypatch):
    backend, path = recovery
    original = backend._kernel_status
    monkeypatch.setattr(backend, "_kernel_status", lambda args:
        OpResult(ok=False, error_type="SSLError", error_message="connection failed")
        if args["kernel"] == "tester/affected-job-r2" else original(args))
    repair(reconcile_jobs=["affected-job"])
    assert json.loads(path.read_text())["jobs"][1]["state"] == "unknown_delivery"
    assert backend.pushes == []


def test_explicit_restart_of_cancelled_run_preserves_both_checkpoints(recovery):
    backend, path = recovery
    state = json.loads(path.read_text())
    state["jobs"][1]["state"] = "failed"
    path.write_text(json.dumps(state))
    backend.finish("tester/affected-job-r2", status="CANCEL_ACKNOWLEDGED")
    backend.outputs["tester/affected-job-r2"] = {"texts/saved.json.gz": "unused"}
    result = repair(restart_cancelled=["affected-job"])
    assert result.status == "ok"
    assert backend.pushes[0]["metadata"]["id"] == "tester/affected-job-r3"
    assert backend.pushes[0]["metadata"]["kernel_sources"] == ["tester/old-checkpoint", "tester/affected-job-r2"]
    assert not any("cancel" in name for name in backend.names())


def test_restart_flag_does_not_restart_a_still_running_job(recovery):
    backend, path = recovery
    state = json.loads(path.read_text())
    state["jobs"][1]["state"] = "failed"
    path.write_text(json.dumps(state))
    backend.statuses["tester/affected-job-r2"] = "RUNNING"
    repair(restart_cancelled=["affected-job"])
    assert json.loads(path.read_text())["jobs"][1]["state"] == "submitted"
    assert backend.pushes == []


def test_recovery_request_remains_idempotent_after_an_automatic_tick(recovery):
    backend, path = recovery
    repair(reconcile_jobs=["affected-job"])
    services.pipeline_tick(owner=OWNER, name="repair", idempotency_key="automatic-2")
    calls = len(backend.calls)
    result = repair(reconcile_jobs=["affected-job"])
    assert result.payload["replayed"] is True
    assert len(backend.calls) == calls
    assert len(backend.pushes) == 1


def test_recovery_key_cannot_be_reused_for_a_different_request(recovery):
    repair(reconcile_jobs=["affected-job"])
    result = repair(restart_cancelled=["affected-job"])
    assert result.status == "invalid_input"
    assert result.payload["error"]["error_code"] == "KAGGLE_RECOVERY_KEY_REUSED"


def test_new_attempt_collision_never_overwrites_an_existing_notebook(recovery):
    backend, path = recovery
    backend.statuses["tester/affected-job-r3"] = "RUNNING"
    repair(reconcile_jobs=["affected-job"])
    assert json.loads(path.read_text())["jobs"][1]["state"] == "unknown_delivery"
    assert backend.pushes == []


DNS_FAILURE = ("HTTPSConnectionPool(host='api.kaggle.com', port=443): Max retries exceeded with url: "
               "/v1/security.OAuthService/IntrospectToken (Caused by NameResolutionError(\"Failed to resolve "
               "'api.kaggle.com' ([Errno -2] Name or service not known)\"))")
RESET_FAILURE = "('Connection aborted.', ConnectionResetError(104, 'Connection reset by peer'))"


@pytest.fixture
def redacted_listing(recovery, monkeypatch):
    backend, path = recovery

    def presence(args):
        return OpResult(ok=True, data={
            "username": "tester", "complete": True, "witness_present": True, "redacted": 19,
            "found": [ref for ref in args["kernels"] if ref in backend.statuses],
        })

    monkeypatch.setattr(backend, "_kernel_presence", presence)

    def fail_with(message):
        state = json.loads(path.read_text())
        state["jobs"][1]["failure"] = message
        path.write_text(json.dumps(state))

    return backend, path, fail_with


def test_redacted_listing_retries_a_push_that_never_reached_kaggle(redacted_listing):
    backend, path, fail_with = redacted_listing
    fail_with(DNS_FAILURE)
    result = repair(reconcile_jobs=["affected-job"])
    assert result.status == "ok"
    job = json.loads(path.read_text())["jobs"][1]
    assert job["run_slug"] == "affected-job-r3"
    assert [push["metadata"]["id"] for push in backend.pushes] == ["tester/affected-job-r3"]
    entry = result.payload["recovery"][0]
    assert entry["reason"] == "verified_non_delivery_before_connection"
    assert entry["redacted_listing_rows"] == 19


@pytest.mark.parametrize("failure", [RESET_FAILURE, "Expecting value: line 1 column 1 (char 0)", None])
def test_redacted_listing_never_retries_a_push_that_may_have_been_sent(redacted_listing, failure):
    backend, path, fail_with = redacted_listing
    fail_with(failure)
    repair(reconcile_jobs=["affected-job"])
    assert json.loads(path.read_text())["jobs"][1]["state"] == "unknown_delivery"
    assert backend.pushes == []


def test_redacted_listing_checks_the_new_slug_directly(redacted_listing, monkeypatch):
    backend, path, fail_with = redacted_listing
    fail_with(DNS_FAILURE)
    backend.statuses["tester/affected-job-r3"] = "RUNNING"
    monkeypatch.setattr(backend, "_kernel_presence", lambda args: OpResult(ok=True, data={
        "username": "tester", "complete": True, "witness_present": True, "redacted": 19, "found": [],
    }))
    repair(reconcile_jobs=["affected-job"])
    assert json.loads(path.read_text())["jobs"][1]["state"] == "unknown_delivery"
    assert backend.pushes == []


def test_redacted_listing_never_restarts_a_cancelled_run(redacted_listing):
    backend, path, _ = redacted_listing
    backend.finish("tester/affected-job-r2", status="CANCEL_ACKNOWLEDGED")
    repair(restart_cancelled=["affected-job"])
    assert backend.pushes == []


def test_ordinary_tick_never_restarts_cancelled_or_uncertain_jobs(recovery):
    backend, path = recovery
    services.pipeline_tick(owner=OWNER, name="repair", idempotency_key="ordinary")
    assert json.loads(path.read_text())["jobs"][1]["state"] == "unknown_delivery"
    assert backend.pushes == []


def test_witness_is_required_before_restarting_cancelled_run(recovery, monkeypatch):
    backend, path = recovery
    backend.finish("tester/affected-job-r2", status="CANCEL_ACKNOWLEDGED")
    monkeypatch.setattr(backend, "_kernel_presence", lambda args: OpResult(ok=True, data={
        "username": "tester", "complete": True, "witness_present": False, "found": [],
    }))
    repair(restart_cancelled=["affected-job"])
    assert backend.pushes == []


QUOTA = "Drive verification/rate/quota page; deferred without bypass"


def quota_summary(**changes):
    summary = {
        "mode": "download", "complete": False, "expected": 10, "downloaded": 4, "progress": 4,
        "deferred": {"reason": QUOTA, "retry_after_seconds": 1800},
        "failures": [{"id": "file-a", "error": QUOTA}],
    }
    summary.update(changes)
    return summary


def bad_file_summary(**changes):
    summary = {
        "mode": "download", "complete": False, "expected": 3, "downloaded": 2, "progress": 2,
        "failures": [{"id": "file-b", "error": "zero_page_pdf"}],
    }
    summary.update(changes)
    return summary


def make_partial(path, summary, **fields):
    state = json.loads(path.read_text())
    job = state["jobs"][1]
    job.update(state="partial", run_slug="affected-job-r2", attempt=2, stalled=2, last_progress=4.0,
               summary=summary, failure="incomplete after 2 attempt(s) without further progress")
    job.update(fields)
    path.write_text(json.dumps(state))


def job_state(path):
    return json.loads(path.read_text())["jobs"][1]


def test_quota_stalled_partial_is_resumed_from_its_checkpoint(recovery):
    backend, path = recovery
    make_partial(path, quota_summary())
    backend.finish("tester/affected-job-r2", {"complete": False, "progress": 4})
    before = time.time()
    result = repair(resume_partial=["affected-job"])
    assert result.status == "ok"
    job = job_state(path)
    assert job["state"] == "pending"
    assert job["run_slug"] == "affected-job-r3"
    assert job["attempt"] == 3
    assert job["stalled"] == 0
    assert job["previous_sources"] == ["affected-job-r2"]
    assert job["not_before"] >= before + 1800
    assert "failure" not in job
    assert backend.pushes == []
    audit = result.payload["recovery"][0]
    assert audit["outcome"] == "queued_continuation"
    assert audit["reason"] == "verified_quota_deferral"


def test_resumed_attempt_is_pushed_once_the_quota_wait_has_passed(recovery):
    backend, path = recovery
    make_partial(path, quota_summary())
    backend.finish("tester/affected-job-r2", {"complete": False, "progress": 4})
    repair(resume_partial=["affected-job"])
    state = json.loads(path.read_text())
    state["jobs"][1]["not_before"] = time.time() - 1
    path.write_text(json.dumps(state))
    services.pipeline_tick(owner=OWNER, name="repair", idempotency_key="after-wait")
    assert backend.pushes[0]["metadata"]["id"] == "tester/affected-job-r3"
    assert backend.pushes[0]["metadata"]["kernel_sources"] == ["tester/affected-job-r2"]


def test_partial_without_a_quota_cause_is_not_resumed(recovery):
    backend, path = recovery
    make_partial(path, {"mode": "extract", "complete": False, "failures": [{"id": "x", "error": "Unresolved character corruption at page 8"}]})
    backend.finish("tester/affected-job-r2", {"complete": False})
    result = repair(resume_partial=["affected-job"])
    assert job_state(path)["state"] == "partial"
    assert result.payload["recovery"][0]["outcome"] == "unresolved"
    assert backend.pushes == []


def test_resume_never_touches_a_run_that_is_still_active(recovery):
    backend, path = recovery
    make_partial(path, quota_summary())
    backend.statuses["tester/affected-job-r2"] = "RUNNING"
    repair(resume_partial=["affected-job"])
    job = job_state(path)
    assert job["state"] == "partial"
    assert job["run_slug"] == "affected-job-r2"


def test_resume_stops_at_the_attempt_limit(recovery):
    backend, path = recovery
    make_partial(path, quota_summary(), attempt=8)
    backend.finish("tester/affected-job-r2", {"complete": False})
    repair(resume_partial=["affected-job"])
    assert job_state(path)["state"] == "partial"
    assert backend.pushes == []


def test_resume_never_reuses_an_existing_attempt_slug(recovery):
    backend, path = recovery
    make_partial(path, quota_summary())
    backend.finish("tester/affected-job-r2", {"complete": False})
    backend.statuses["tester/affected-job-r3"] = "RUNNING"
    repair(resume_partial=["affected-job"])
    assert job_state(path)["state"] == "partial"
    assert backend.pushes == []


def test_resume_requires_a_verified_owned_list(recovery, monkeypatch):
    backend, path = recovery
    make_partial(path, quota_summary())
    backend.finish("tester/affected-job-r2", {"complete": False})
    monkeypatch.setattr(backend, "_kernel_presence", lambda args: OpResult(ok=True, data={
        "username": "tester", "complete": False, "witness_present": True, "found": [],
    }))
    repair(resume_partial=["affected-job"])
    assert job_state(path)["state"] == "partial"


def test_only_permanently_unavailable_files_are_waived(recovery):
    backend, path = recovery
    make_partial(path, bad_file_summary())
    result = repair(accept_unavailable=["affected-job"])
    assert result.status == "ok"
    job = job_state(path)
    assert job["state"] == "complete"
    assert job["waived"] == [{"id": "file-b", "error": "zero_page_pdf"}]
    assert "failure" not in job
    audit = result.payload["recovery"][0]
    assert audit["outcome"] == "waived_unavailable"
    assert audit["waived"] == job["waived"]
    assert backend.pushes == []


def test_http_404_download_is_a_permanent_failure(recovery):
    backend, path = recovery
    error = "404 Client Error: Not Found for url: https://drive.usercontent.google.com/download"
    make_partial(path, bad_file_summary(failures=[{"id": "gone", "error": error}]))
    repair(accept_unavailable=["affected-job"])
    assert job_state(path)["state"] == "complete"


def test_waiver_only_arms_the_job_while_quota_files_are_still_missing(recovery):
    backend, path = recovery
    mixed = bad_file_summary(expected=10, downloaded=4, deferred={"reason": QUOTA, "retry_after_seconds": 1800},
                             failures=[{"id": "file-b", "error": "zero_page_pdf"}, {"id": "file-c", "error": QUOTA}])
    make_partial(path, mixed)
    result = repair(accept_unavailable=["affected-job"])
    assert job_state(path)["state"] == "partial"
    assert "waived" not in job_state(path)
    assert job_state(path)["waive_unavailable"] is True
    assert result.payload["recovery"][0]["outcome"] == "armed"


def test_waiver_only_arms_the_job_when_missing_files_are_not_all_accounted_for(recovery):
    backend, path = recovery
    make_partial(path, bad_file_summary(expected=9))
    repair(accept_unavailable=["affected-job"])
    assert job_state(path)["state"] == "partial"


def test_download_waiver_rules_do_not_apply_to_an_extraction_job(recovery):
    backend, path = recovery
    make_partial(path, {"mode": "extract", "complete": False, "expected": 3, "downloaded": 2,
                        "failures": [{"id": "file-b", "error": "zero_page_pdf"}]})
    repair(accept_unavailable=["affected-job"])
    assert job_state(path)["state"] == "partial"


def test_waiver_is_refused_for_a_job_that_cannot_be_armed(recovery):
    backend, path = recovery
    result = repair(accept_unavailable=["affected-job"])
    assert job_state(path)["state"] == "unknown_delivery"
    assert "waive_unavailable" not in job_state(path)
    assert result.payload["recovery"][0]["outcome"] == "unresolved"


def test_a_job_cannot_appear_in_two_recovery_lists(recovery):
    result = repair(resume_partial=["affected-job"], accept_unavailable=["affected-job"])
    assert result.status == "invalid_input"
    assert result.payload["error"]["error_code"] == "KAGGLE_RECOVERY_INVALID"


def test_recovery_key_cannot_swap_resume_for_waiver(recovery):
    backend, path = recovery
    make_partial(path, quota_summary())
    backend.finish("tester/affected-job-r2", {"complete": False})
    repair(resume_partial=["affected-job"])
    result = repair(accept_unavailable=["affected-job"])
    assert result.status == "invalid_input"
    assert result.payload["error"]["error_code"] == "KAGGLE_RECOVERY_KEY_REUSED"


def test_recovery_digest_for_the_original_two_lists_is_unchanged(recovery):
    backend, path = recovery
    backend.statuses["tester/affected-job-r2"] = "RUNNING"
    repair(reconcile_jobs=["affected-job"])
    stored = json.loads(path.read_text())["recovery_requests"]["repair-1"]["digest"]
    assert stored == sha256_text(json.dumps([["affected-job"], []]))
    replay = repair(reconcile_jobs=["affected-job"])
    assert replay.payload["replayed"] is True


EXTRACT_ERROR = "Source file was not downloaded successfully"


def extract_summary(**changes):
    summary = {
        "mode": "extract", "complete": False, "expected": 3, "processed": 3, "partial": 0, "failed": 1,
        "complete_pdfs": 1, "progress": 10,
        "failures": [{"id": "file-b", "error": EXTRACT_ERROR}],
    }
    summary.update(changes)
    return summary


def depend_on_waived_download(path, waived=("file-b",)):
    state = json.loads(path.read_text())
    state["jobs"][0]["waived"] = [{"id": item, "error": "zero_page_pdf"} for item in waived]
    state["jobs"][1]["depends_on"] = ["witness-job"]
    path.write_text(json.dumps(state))


def test_armed_download_is_waived_when_its_run_finishes_with_only_permanent_failures(recovery):
    backend, path = recovery
    state = json.loads(path.read_text())
    state["jobs"][1].update(state="submitted", run_slug="affected-job-r2", remote_status="RUNNING")
    path.write_text(json.dumps(state))
    backend.statuses["tester/affected-job-r2"] = "RUNNING"
    result = repair(accept_unavailable=["affected-job"])
    assert result.payload["recovery"][0]["outcome"] == "armed"
    backend.finish("tester/affected-job-r2", bad_file_summary())
    services.pipeline_tick(owner=OWNER, name="repair", idempotency_key="after-run")
    job = job_state(path)
    assert job["state"] == "complete"
    assert job["waived"] == [{"id": "file-b", "error": "zero_page_pdf"}]
    assert backend.pushes == []


def test_unarmed_download_is_never_waived_automatically(recovery):
    backend, path = recovery
    state = json.loads(path.read_text())
    state["jobs"][1].update(state="submitted", run_slug="affected-job-r2", remote_status="RUNNING")
    path.write_text(json.dumps(state))
    backend.finish("tester/affected-job-r2", bad_file_summary())
    services.pipeline_tick(owner=OWNER, name="repair", idempotency_key="after-run")
    job = job_state(path)
    assert job["state"] != "complete"
    assert "waived" not in job


def test_extraction_is_waived_only_for_files_waived_upstream(recovery):
    backend, path = recovery
    depend_on_waived_download(path)
    make_partial(path, extract_summary())
    result = repair(accept_unavailable=["affected-job"])
    job = job_state(path)
    assert job["state"] == "complete"
    assert job["waived"] == [{"id": "file-b", "error": EXTRACT_ERROR}]
    assert result.payload["recovery"][0]["outcome"] == "waived_unavailable"


@pytest.mark.parametrize("changes", [
    {"failures": [{"id": "other-file", "error": EXTRACT_ERROR}]},
    {"failures": [{"id": "file-b", "error": "Image page has unresolved OCR quality at page 4"}]},
    {"failed": 2},
    {"processed": 2},
    {"partial": 1},
    {"deferred": {"retry_after_seconds": 60}},
])
def test_extraction_waiver_only_arms_the_job_for_anything_else(recovery, changes):
    backend, path = recovery
    depend_on_waived_download(path)
    make_partial(path, extract_summary(**changes))
    result = repair(accept_unavailable=["affected-job"])
    assert job_state(path)["state"] == "partial"
    assert "waived" not in job_state(path)
    assert result.payload["recovery"][0]["outcome"] == "armed"


def test_extraction_waiver_needs_a_waived_dependency(recovery):
    backend, path = recovery
    state = json.loads(path.read_text())
    state["jobs"][1]["depends_on"] = ["witness-job"]
    path.write_text(json.dumps(state))
    make_partial(path, extract_summary())
    repair(accept_unavailable=["affected-job"])
    assert job_state(path)["state"] == "partial"


OCR_ERROR = "Image page has unresolved OCR quality at page 4"
CORRUPT_ERROR = "Unresolved character corruption at page 9"
CONVERSION_ERROR = "Partial/failed document conversion: ConversionStatus.PARTIAL_SUCCESS"


def quality_summary(errors, **changes):
    failures = [{"id": f"file-{index}", "error": error} for index, error in enumerate(errors)]
    return extract_summary(failures=failures, failed=len(failures), expected=len(failures) + 2,
                           processed=len(failures) + 2, **changes)


def test_unextractable_extraction_accepts_every_quality_refusal(recovery):
    backend, path = recovery
    make_partial(path, quality_summary([OCR_ERROR, CORRUPT_ERROR, CONVERSION_ERROR]))
    result = repair(accept_unextractable=["affected-job"])
    job = job_state(path)
    assert job["state"] == "complete"
    assert [item["id"] for item in job["waived"]] == ["file-0", "file-1", "file-2"]
    assert result.payload["recovery"][0]["outcome"] == "waived_unavailable"


def test_unextractable_extraction_also_accepts_files_waived_upstream(recovery):
    backend, path = recovery
    depend_on_waived_download(path, waived=("file-b",))
    summary = extract_summary(failed=2, failures=[{"id": "file-b", "error": EXTRACT_ERROR}, {"id": "file-c", "error": OCR_ERROR}])
    make_partial(path, summary)
    repair(accept_unextractable=["affected-job"])
    assert job_state(path)["state"] == "complete"


@pytest.mark.parametrize("errors", [
    ["Disk reserve reached; split this shard and resume"],
    ["TimeoutError: conversion exceeded the deadline"],
    [OCR_ERROR, "Source file was not downloaded successfully"],
])
def test_unextractable_extraction_refuses_unrecognised_or_unwaived_failures(recovery, errors):
    backend, path = recovery
    make_partial(path, quality_summary(errors))
    result = repair(accept_unextractable=["affected-job"])
    assert job_state(path)["state"] == "partial"
    assert "waived" not in job_state(path)
    assert result.payload["recovery"][0]["outcome"] == "armed"


def test_truncated_failure_list_is_never_waived(recovery):
    backend, path = recovery
    summary = quality_summary([OCR_ERROR] * 20)
    summary.update(failed=25, expected=27, processed=27)
    make_partial(path, summary)
    result = repair(accept_unextractable=["affected-job"])
    assert job_state(path)["state"] == "partial"
    assert "truncated" in result.payload["recovery"][0]["reason"]


def test_unextractable_flag_does_not_waive_a_download_shard(recovery):
    backend, path = recovery
    make_partial(path, bad_file_summary())
    repair(accept_unextractable=["affected-job"])
    assert job_state(path)["state"] == "partial"
    assert "waived" not in job_state(path)


def test_unavailable_flag_alone_never_accepts_quality_refusals(recovery):
    backend, path = recovery
    make_partial(path, quality_summary([OCR_ERROR]))
    repair(accept_unavailable=["affected-job"])
    assert job_state(path)["state"] == "partial"
    assert "waived" not in job_state(path)


def test_armed_extraction_is_waived_when_its_run_finishes(recovery):
    backend, path = recovery
    state = json.loads(path.read_text())
    state["jobs"][1].update(state="submitted", run_slug="affected-job-r2", remote_status="RUNNING")
    path.write_text(json.dumps(state))
    backend.statuses["tester/affected-job-r2"] = "RUNNING"
    repair(accept_unextractable=["affected-job"])
    backend.finish("tester/affected-job-r2", quality_summary([OCR_ERROR, CORRUPT_ERROR]))
    services.pipeline_tick(owner=OWNER, name="repair", idempotency_key="after-run")
    job = job_state(path)
    assert job["state"] == "complete"
    assert len(job["waived"]) == 2
    assert backend.pushes == []


def test_recovery_digest_for_earlier_four_list_requests_is_unchanged(recovery):
    backend, path = recovery
    make_partial(path, bad_file_summary())
    repair(accept_unavailable=["affected-job"])
    stored = json.loads(path.read_text())["recovery_requests"]["repair-1"]["digest"]
    assert stored == sha256_text(json.dumps([[], [], [], ["affected-job"]]))
    assert repair(accept_unavailable=["affected-job"]).payload["replayed"] is True


def test_a_job_cannot_be_in_both_waiver_lists(recovery):
    result = repair(accept_unavailable=["affected-job"], accept_unextractable=["affected-job"])
    assert result.status == "invalid_input"


RUN = "tester/affected-job-r2"
DISK_ERROR = "Disk reserve reached; split this shard and resume"


def manifest_run(errors, listed=20):
    records = [{"id": f"file-{index}", "status": "failed", "error": error, "name": f"doc-{index}.pdf",
                "nama_perusahaan": f"PT {index}", "sector": "Energy", "tahun": 2023}
               for index, error in enumerate(errors)]
    records += [{"id": f"ok-{index}", "status": "complete"} for index in range(3)]
    summary = extract_summary(expected=len(records), processed=len(records), failed=len(errors),
                              failures=[{"id": item["id"], "error": item["error"]} for item in records[:listed] if item["status"] == "failed"])
    return summary, {"records": records}


def publish(backend, manifest, name="results.json"):
    backend.finish(RUN, {"complete": False})
    backend.outputs[RUN][name] = manifest


def test_failure_list_beyond_twenty_is_completed_from_the_results_manifest(recovery):
    backend, path = recovery
    summary, manifest = manifest_run([OCR_ERROR] * 25)
    make_partial(path, summary)
    publish(backend, manifest)
    repair(accept_unextractable=["affected-job"])
    job = job_state(path)
    assert job["state"] == "complete"
    assert len(job["waived"]) == 25
    assert job["waived"][24] == {"id": "file-24", "error": OCR_ERROR, "name": "doc-24.pdf",
                                 "company": "PT 24", "sector": "Energy", "year": 2023}


def test_unrecognised_failure_hidden_beyond_the_listed_twenty_blocks_the_waiver(recovery):
    backend, path = recovery
    summary, manifest = manifest_run([OCR_ERROR] * 24 + [DISK_ERROR])
    make_partial(path, summary)
    publish(backend, manifest)
    result = repair(accept_unextractable=["affected-job"])
    assert job_state(path)["state"] == "partial"
    assert result.payload["recovery"][0]["outcome"] == "armed"


def test_manifest_that_disagrees_with_the_summary_is_ignored(recovery):
    backend, path = recovery
    summary, manifest = manifest_run([OCR_ERROR] * 25)
    manifest["records"][0]["id"] = "someone-else"
    make_partial(path, summary)
    publish(backend, manifest)
    repair(accept_unextractable=["affected-job"])
    assert job_state(path)["state"] == "partial"


def test_truncated_manifest_read_is_ignored(recovery, monkeypatch):
    backend, path = recovery
    summary, manifest = manifest_run([OCR_ERROR] * 25)
    make_partial(path, summary)
    publish(backend, manifest)
    original = backend._kernel_output

    def clipped(args):
        result = original(args)
        for entry in ((result.data or {}).get("reads") or {}).values():
            if entry:
                entry["truncated"] = True
        return result

    monkeypatch.setattr(backend, "_kernel_output", clipped)
    repair(accept_unextractable=["affected-job"])
    assert job_state(path)["state"] == "partial"


def test_waiver_without_a_manifest_still_works_for_a_complete_failure_list(recovery):
    backend, path = recovery
    make_partial(path, quality_summary([OCR_ERROR]))
    repair(accept_unextractable=["affected-job"])
    assert job_state(path)["waived"] == [{"id": "file-0", "error": OCR_ERROR}]


def test_download_waiver_is_enriched_from_the_downloads_manifest(recovery):
    backend, path = recovery
    make_partial(path, bad_file_summary())
    publish(backend, {"expected": 3, "records": [
        {"id": "file-b", "download_status": "failed", "error": "zero_page_pdf", "name": "TOBA SR 2023.pdf",
         "sector": "Energy", "folder_year": "2023"},
        {"id": "ok-1", "download_status": "complete"},
    ]}, name="downloads.json")
    repair(accept_unavailable=["affected-job"])
    assert job_state(path)["waived"] == [{"id": "file-b", "error": "zero_page_pdf", "name": "TOBA SR 2023.pdf",
                                          "sector": "Energy", "year": "2023"}]


def test_armed_run_with_more_than_twenty_failures_is_waived_when_it_finishes(recovery):
    backend, path = recovery
    state = json.loads(path.read_text())
    state["jobs"][1].update(state="submitted", run_slug="affected-job-r2", remote_status="RUNNING")
    path.write_text(json.dumps(state))
    backend.statuses[RUN] = "RUNNING"
    repair(accept_unextractable=["affected-job"])
    summary, manifest = manifest_run([OCR_ERROR] * 30)
    backend.finish(RUN, summary)
    backend.outputs[RUN]["results.json"] = manifest
    services.pipeline_tick(owner=OWNER, name="repair", idempotency_key="after-run")
    job = job_state(path)
    assert job["state"] == "complete"
    assert len(job["waived"]) == 30
    assert len(json.dumps(job["summary"])) < 7000
    assert backend.pushes == []


def test_unarmed_run_never_reads_a_manifest(recovery):
    backend, path = recovery
    state = json.loads(path.read_text())
    state["jobs"][1].update(state="submitted", run_slug="affected-job-r2", remote_status="RUNNING")
    path.write_text(json.dumps(state))
    summary, manifest = manifest_run([OCR_ERROR] * 25)
    backend.finish(RUN, summary)
    backend.outputs[RUN]["results.json"] = manifest
    services.pipeline_tick(owner=OWNER, name="repair", idempotency_key="after-run")
    wanted = [args.get("read") for name, args in backend.calls if name == "kernel_output"]
    assert wanted
    assert all("results.json" not in (read or []) for read in wanted)
    assert "waived" not in job_state(path)


def test_requeue_back_accepts_a_possibly_sent_push_under_a_redacted_listing(redacted_listing):
    backend, path, fail_with = redacted_listing
    fail_with(RESET_FAILURE)
    result = repair(requeue_back=["affected-job"])
    assert result.status == "ok"
    job = json.loads(path.read_text())["jobs"][1]
    assert job["run_slug"] == "affected-job-r3"
    assert job["queue_rank"] == 1
    assert [push["metadata"]["id"] for push in backend.pushes] == ["tester/affected-job-r3"]
    entry = result.payload["recovery"][0]
    assert entry["reason"] == "owner_accepted_redacted_listing_risk"
    assert entry["queued_at_back"] is True
    assert entry["redacted_listing_rows"] == 19


def test_requeue_back_needs_a_verified_complete_listing(redacted_listing, monkeypatch):
    backend, path, fail_with = redacted_listing
    fail_with(RESET_FAILURE)
    monkeypatch.setattr(backend, "_kernel_presence", lambda args: OpResult(ok=True, data={
        "username": "tester", "complete": False, "witness_present": True, "redacted": 19, "found": [],
    }))
    repair(requeue_back=["affected-job"])
    job = json.loads(path.read_text())["jobs"][1]
    assert job["state"] == "unknown_delivery"
    assert "queue_rank" not in job
    assert backend.pushes == []


def test_requeue_back_never_requeues_a_kernel_that_is_listed(redacted_listing, monkeypatch):
    backend, path, fail_with = redacted_listing
    fail_with(RESET_FAILURE)
    monkeypatch.setattr(backend, "_kernel_presence", lambda args: OpResult(ok=True, data={
        "username": "tester", "complete": True, "witness_present": True, "redacted": 19,
        "found": ["tester/affected-job-r2"],
    }))
    repair(requeue_back=["affected-job"])
    assert json.loads(path.read_text())["jobs"][1]["state"] == "unknown_delivery"
    assert backend.pushes == []


def test_requeue_back_checks_the_new_slug_directly(redacted_listing):
    backend, path, fail_with = redacted_listing
    fail_with(RESET_FAILURE)
    backend.statuses["tester/affected-job-r3"] = "RUNNING"
    repair(requeue_back=["affected-job"])
    assert json.loads(path.read_text())["jobs"][1]["state"] == "unknown_delivery"
    assert backend.pushes == []


def test_requeue_back_adopts_a_kernel_that_exists_instead_of_requeuing(redacted_listing):
    backend, path, fail_with = redacted_listing
    fail_with(RESET_FAILURE)
    backend.statuses["tester/affected-job-r2"] = "RUNNING"
    repair(requeue_back=["affected-job"])
    job = json.loads(path.read_text())["jobs"][1]
    assert job["state"] == "submitted"
    assert job["run_slug"] == "affected-job-r2"
    assert "queue_rank" not in job
    assert backend.pushes == []


def test_default_reconcile_still_refuses_a_possibly_sent_push_under_a_redacted_listing(redacted_listing):
    backend, path, fail_with = redacted_listing
    fail_with(RESET_FAILURE)
    repair(reconcile_jobs=["affected-job"])
    assert json.loads(path.read_text())["jobs"][1]["state"] == "unknown_delivery"
    assert backend.pushes == []


def test_requeue_back_digest_covers_all_six_lists(recovery):
    backend, path = recovery
    repair(requeue_back=["affected-job"])
    stored = json.loads(path.read_text())["recovery_requests"]["repair-1"]["digest"]
    assert stored == sha256_text(json.dumps([[], [], [], [], [], ["affected-job"]]))


def test_a_job_cannot_be_requeued_back_and_reconciled_in_one_request(recovery):
    result = repair(reconcile_jobs=["affected-job"], requeue_back=["affected-job"])
    assert result.status == "invalid_input"
    assert result.payload["error"]["error_code"] == "KAGGLE_RECOVERY_INVALID"


def test_jobs_with_a_back_rank_are_submitted_after_the_others(fake_backend, worker_file, kaggle_workspace):
    services.pipeline_plan(owner=OWNER, name="order", limits={"cpu": 1, "gpu": 0}, jobs=[
        {"slug": "first-job", "source_path": "worker.py"},
        {"slug": "second-job", "source_path": "worker.py"},
    ])
    path = kaggle_workspace / "pipelines/order.json"
    state = json.loads(path.read_text())
    state["jobs"][0]["queue_rank"] = 1
    path.write_text(json.dumps(state))
    services.pipeline_tick(owner=OWNER, name="order", idempotency_key="order-1")
    assert [push["metadata"]["id"] for push in fake_backend.pushes] == ["tester/second-job"]
