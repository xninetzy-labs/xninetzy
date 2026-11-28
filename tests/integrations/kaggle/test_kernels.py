from __future__ import annotations

import json

from xninetzy.integrations.kaggle import services as kaggle_services
from xninetzy.integrations.kaggle.backend import KaggleBackendError

OWNER = "test-owner"


def push(**overrides):
    arguments = {
        "owner": OWNER,
        "slug": "my-first-job",
        "idempotency_key": "key-1",
        "source": "print(JOB['n'])\n",
        "job": {"n": 3},
    }
    arguments.update(overrides)
    return kaggle_services.kernel_push(**arguments)


def test_push_submits_private_script_kernel_with_job_prelude(fake_backend) -> None:
    result = push()
    assert result.status == "submitted"
    assert result.payload["slug"] == "tester/my-first-job"
    assert result.payload["replayed"] is False
    assert result.payload["url"].endswith("tester/my-first-job")
    sent = fake_backend.pushes[0]
    assert sent["metadata"]["is_private"] is True
    assert sent["metadata"]["kernel_type"] == "script"
    assert sent["metadata"]["id"] == "tester/my-first-job"
    assert sent["metadata"]["enable_gpu"] is False
    assert sent["accelerator"] is None
    assert sent["code"].startswith("JOB = {")
    assert "'n': 3" in sent["code"].splitlines()[0]
    assert "'time_budget_seconds': 3600" in sent["code"].splitlines()[0]
    assert sent["code"].endswith("print(JOB['n'])\n")
    assert sent["timeout"] == "3840"


def test_push_job_prelude_is_valid_python_for_json_values(fake_backend) -> None:
    push(job={"flag": True, "none": None, "items": [1, "a"], "nested": {"k": 1.5}})
    namespace: dict = {}
    exec(fake_backend.pushes[0]["code"].splitlines()[0], namespace)
    assert namespace["JOB"]["flag"] is True
    assert namespace["JOB"]["none"] is None
    assert namespace["JOB"]["nested"] == {"k": 1.5}


def test_push_keeps_future_imports_first(fake_backend) -> None:
    push(source="from __future__ import annotations\nprint(JOB)\n")
    code = fake_backend.pushes[0]["code"]
    assert code.splitlines()[0] == "from __future__ import annotations"
    compile(code, "worker.py", "exec")


def test_push_gpu_requests_accelerator_and_qualifies_kernel_sources(fake_backend) -> None:
    result = push(
        gpu=True,
        dataset_sources=["olistbr/brazilian-ecommerce"],
        kernel_sources=["upstream-job", "other/upstream-two"],
    )
    assert result.status == "submitted"
    sent = fake_backend.pushes[0]
    assert sent["metadata"]["enable_gpu"] is True
    assert sent["accelerator"] == "NvidiaTeslaT4"
    assert sent["metadata"]["kernel_sources"] == ["tester/upstream-job", "other/upstream-two"]
    assert sent["metadata"]["dataset_sources"] == ["olistbr/brazilian-ecommerce"]


def test_same_key_and_payload_replays_without_second_push(fake_backend) -> None:
    first = push()
    second = push()
    assert first.status == "submitted"
    assert second.status == "submitted"
    assert second.payload["replayed"] is True
    assert second.payload["url"] == first.payload["url"]
    assert len(fake_backend.pushes) == 1


def test_same_key_with_different_payload_is_rejected(fake_backend) -> None:
    push()
    changed = push(source="print('different')\n")
    assert changed.status == "rejected"
    assert changed.payload["error"]["error_code"] == "KAGGLE_IDEMPOTENCY_KEY_REUSED"
    assert len(fake_backend.pushes) == 1


def test_timeout_leaves_unknown_delivery_and_never_replays(fake_backend) -> None:
    fake_backend.push_raises = KaggleBackendError("KAGGLE_RUNNER_TIMEOUT", "timed out")
    first = push()
    assert first.status == "unknown_delivery"
    fake_backend.push_raises = None
    again = push()
    assert again.status == "unknown_delivery"
    assert again.payload["error"]["error_code"] == "KAGGLE_DELIVERY_UNKNOWN"
    assert fake_backend.pushes == []
    assert fake_backend.names().count("kernel_push") == 1


def test_rejected_push_may_be_retried_with_the_same_key(fake_backend) -> None:
    fake_backend.push_errors = ["Maximum batch CPU session count reached"]
    rejected = push()
    assert rejected.status == "rejected"
    assert "Maximum batch" in rejected.payload["error"]["message"]
    retried = push()
    assert retried.status == "submitted"
    assert len(fake_backend.pushes) == 1


def test_missing_sdk_is_an_error_not_a_delivery(fake_backend) -> None:
    fake_backend.push_raises = KaggleBackendError("KAGGLE_SDK_MISSING", "no sdk")
    result = push()
    assert result.status == "error"
    fake_backend.push_raises = None
    assert push().status == "submitted"


def test_push_validates_inputs_before_any_network_call(fake_backend, kaggle_workspace) -> None:
    assert push(slug="Bad Slug").status == "invalid_input"
    assert push(slug="abcd").status == "invalid_input"
    assert push(idempotency_key="").status == "invalid_input"
    assert push(time_budget_seconds=10).status == "invalid_input"
    assert push(source=None, source_path=None).status == "invalid_input"
    assert push(source="x", source_path="y").status == "invalid_input"
    assert push(source="   \n").status == "invalid_input"
    assert push(dataset_sources=["not a dataset"]).status == "invalid_input"
    assert push(job={"bad": object()}).status == "invalid_input"
    assert fake_backend.calls == []
    assert fake_backend.pushes == []


def test_source_path_must_live_inside_allowed_roots(fake_backend, tmp_path, worker_file) -> None:
    outside = tmp_path / "outside.py"
    outside.write_text("print(1)\n")
    refused = push(source=None, source_path=str(outside))
    assert refused.status == "invalid_input"
    assert refused.payload["error"]["error_code"] == "KAGGLE_SOURCE_OUTSIDE_ROOTS"
    accepted = push(source=None, source_path=str(worker_file), idempotency_key="key-path")
    assert accepted.status == "submitted"
    assert accepted.payload["source_sha256"]


def test_extra_source_roots_extend_allowed_locations(fake_backend, tmp_path, monkeypatch) -> None:
    from xninetzy.core.config import get_settings

    extra = tmp_path / "extra-root"
    extra.mkdir()
    (extra / "w.py").write_text("print(1)\n")
    monkeypatch.setenv("KAGGLE_SOURCE_ROOTS", str(extra))
    get_settings.cache_clear()
    result = push(source=None, source_path=str(extra / "w.py"))
    assert result.status == "submitted"


def test_symlink_escape_from_workspace_is_blocked(fake_backend, tmp_path, kaggle_workspace) -> None:
    secret = tmp_path / "secret.py"
    secret.write_text("print('secret')\n")
    link = kaggle_workspace / "link.py"
    link.symlink_to(secret)
    result = push(source=None, source_path=str(link))
    assert result.status == "invalid_input"
    assert result.payload["error"]["error_code"] == "KAGGLE_SOURCE_OUTSIDE_ROOTS"


def test_push_requires_authentication(no_credentials, kaggle_workspace) -> None:
    assert push().status == "auth_required"


def test_status_reports_terminal_and_success_flags(fake_backend) -> None:
    fake_backend.statuses["tester/job-a"] = "RUNNING"
    running = kaggle_services.kernel_status(owner=OWNER, slug="job-a")
    assert running.payload["status"] == "RUNNING"
    assert running.payload["terminal"] is False
    fake_backend.finish("tester/job-a")
    done = kaggle_services.kernel_status(owner=OWNER, slug="tester/job-a")
    assert done.payload["terminal"] is True
    assert done.payload["succeeded"] is True


def test_status_failure_message_is_surfaced(fake_backend) -> None:
    fake_backend.failures["tester/job-b"] = "OOM"
    fake_backend.statuses["tester/job-b"] = "ERROR"
    result = kaggle_services.kernel_status(owner=OWNER, slug="job-b")
    assert result.payload["terminal"] is True
    assert result.payload["succeeded"] is False
    assert result.payload["failure_message"] == "OOM"


def test_status_of_unknown_kernel_is_not_accessible(fake_backend) -> None:
    result = kaggle_services.kernel_status(owner=OWNER, slug="nobody/never-pushed")
    assert result.status == "not_accessible"


def test_output_parses_json_reads_and_marks_missing_files(fake_backend) -> None:
    fake_backend.finish("tester/job-a", {"complete": True, "n": 2})
    fake_backend.outputs["tester/job-a"]["notes.txt"] = "plain text"
    result = kaggle_services.kernel_output(
        owner=OWNER,
        slug="job-a",
        read=["summary.json", "notes.txt", "absent.json"],
        log_tail_chars=100,
    )
    reads = result.payload["reads"]
    assert reads["summary.json"]["json"] == {"complete": True, "n": 2}
    assert reads["notes.txt"]["text"] == "plain text"
    assert reads["absent.json"] is None
    assert result.payload["log_tail"] == "log line"
    assert "summary.json" in result.payload["files"]


def test_output_splits_read_budget_across_requested_files(fake_backend) -> None:
    fake_backend.finish("tester/job-a", {"complete": True})
    kaggle_services.kernel_output(owner=OWNER, slug="job-a", read=["a", "b", "c"], max_read_bytes=1_000_000)
    sent = fake_backend.calls[-1][1]
    assert sent["max_read_bytes"] <= 8_000
    assert len(sent["read"]) == 3


def test_output_live_log_is_requested_and_attached(fake_backend) -> None:
    fake_backend.finish("tester/job-a")
    result = kaggle_services.kernel_output(owner=OWNER, slug="job-a", live_log_seconds=5)
    assert result.payload["log_tail"] == "live log"
    assert "kernel_logs" in fake_backend.names()


def test_tool_wrapper_serializes_push_result(fake_backend) -> None:
    from xninetzy.tools.ecosystem import kaggle_tools

    parsed = json.loads(
        kaggle_tools.kaggle_kernel_push(
            slug="tool-wrapped-job",
            idempotency_key="tool-key",
            source="print(1)\n",
            sender_id=OWNER,
        )
    )
    assert parsed["summary"]["status"] == "submitted"
    assert parsed["summary"]["payload"]["slug"] == "tester/tool-wrapped-job"
