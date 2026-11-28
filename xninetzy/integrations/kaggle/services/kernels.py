from __future__ import annotations

import json
import time
from typing import Any, Sequence

from xninetzy.integrations.kaggle import backend as backend_module
from xninetzy.integrations.kaggle.auth_adapter import KaggleAuthContext, resolve_kaggle_auth
from xninetzy.integrations.kaggle.backend import KaggleBackendError
from xninetzy.integrations.kaggle.services.base import (
    KaggleOperationResult,
    envelope,
    op_failure,
    run_operations,
)
from xninetzy.integrations.kaggle.workspace import (
    DATASET_REF_PATTERN,
    SLUG_PATTERN,
    WorkspaceError,
    locked,
    read_json,
    resolve_source_path,
    sha256_text,
    subdir,
    write_json,
)

TERMINAL_STATUSES = frozenset({"COMPLETE", "ERROR", "CANCELLED", "CANCELED", "CANCEL_ACKNOWLEDGED"})
FAILED_STATUSES = frozenset({"ERROR", "CANCELLED", "CANCELED", "CANCEL_ACKNOWLEDGED"})
MIN_SLUG = 5
MAX_SLUG = 50
MAX_SOURCE_BYTES = 1_048_576
MAX_JOB_BYTES = 32_768
MAX_READ_TOTAL = 24_000
DEFAULT_ACCELERATOR = "NvidiaTeslaT4"
_USERNAMES: dict[tuple[str, str], str] = {}


def reset_username_cache() -> None:
    _USERNAMES.clear()


def valid_slug(value: str) -> bool:
    return MIN_SLUG <= len(value) <= MAX_SLUG and bool(SLUG_PATTERN.match(value))


def username_for(owner: str, account: str, auth: KaggleAuthContext) -> str | None:
    key = (owner, account)
    if key in _USERNAMES:
        return _USERNAMES[key]
    try:
        results = backend_module.get_backend().run([("whoami", {})], bearer_token=auth.bearer_token)
    except KaggleBackendError:
        return None
    if results and results[0].ok:
        name = (results[0].data or {}).get("username")
        if isinstance(name, str) and name:
            _USERNAMES[key] = name
            return name
    return None


def qualify(reference: str, username: str) -> str:
    return reference if "/" in reference else f"{username}/{reference}"


def _invalid(operation: str, auth: KaggleAuthContext, code: str, message: str) -> KaggleOperationResult:
    return envelope("invalid_input", operation, auth, {"error": {"error_code": code, "message": message}})


def _ledger_path():
    return subdir("ledger") / "pushes.json"


def _compose_code(code: str, job: dict[str, Any] | None, budget: int) -> tuple[str, str]:
    digest = sha256_text(code)
    body = {"time_budget_seconds": budget, **(job or {}), "source_sha256": digest}
    prelude = "JOB = " + repr(json.loads(json.dumps(body))) + "\n"
    lines = code.splitlines(keepends=True)
    insert_at = 0
    for index, line in enumerate(lines[:60]):
        if line.startswith("from __future__ import"):
            insert_at = index + 1
    return "".join(lines[:insert_at]) + prelude + "".join(lines[insert_at:]), digest


def _load_code(source: str | None, source_path: str | None) -> str:
    if bool(source) == bool(source_path):
        raise WorkspaceError("KAGGLE_SOURCE_REQUIRED", "provide exactly one of source or source_path")
    code = source if source else resolve_source_path(str(source_path)).read_text(encoding="utf-8")
    if len(code.encode("utf-8")) > MAX_SOURCE_BYTES:
        raise WorkspaceError("KAGGLE_SOURCE_TOO_LARGE", "kernel source exceeds 1 MiB")
    if not code.strip():
        raise WorkspaceError("KAGGLE_SOURCE_REQUIRED", "kernel source is empty")
    return code


def push(
    *,
    owner: str,
    slug: str,
    idempotency_key: str,
    account: str = "default",
    source: str | None = None,
    source_path: str | None = None,
    job: dict[str, Any] | None = None,
    gpu: bool = False,
    accelerator: str = "",
    internet: bool = True,
    dataset_sources: Sequence[str] = (),
    kernel_sources: Sequence[str] = (),
    time_budget_seconds: int = 3600,
    username: str | None = None,
) -> KaggleOperationResult:
    auth = resolve_kaggle_auth(owner=owner, account=account)
    if not auth.authenticated:
        return envelope("auth_required", "kernel_push", auth)
    slug = slug.strip()
    key = idempotency_key.strip()
    if not valid_slug(slug):
        return _invalid("kernel_push", auth, "KAGGLE_SLUG_INVALID", f"slug must be lowercase letters, digits and hyphens, {MIN_SLUG}-{MAX_SLUG} characters")
    if not key or len(key) > 160:
        return _invalid("kernel_push", auth, "KAGGLE_IDEMPOTENCY_KEY_REQUIRED", "idempotency_key is required (max 160 characters)")
    if not 60 <= int(time_budget_seconds) <= 43_200:
        return _invalid("kernel_push", auth, "KAGGLE_TIME_BUDGET_INVALID", "time_budget_seconds must be between 60 and 43200")
    for dataset in dataset_sources:
        if not DATASET_REF_PATTERN.match(dataset):
            return _invalid("kernel_push", auth, "KAGGLE_DATASET_REF_INVALID", f"dataset source {dataset!r} must look like owner/dataset-slug")
    try:
        code = _load_code(source, source_path)
        if job is not None and len(json.dumps(job).encode("utf-8")) > MAX_JOB_BYTES:
            raise WorkspaceError("KAGGLE_JOB_TOO_LARGE", "job parameters exceed 32 KiB")
        composed, source_digest = _compose_code(code, job, int(time_budget_seconds))
    except WorkspaceError as exc:
        return envelope("invalid_input", "kernel_push", auth, {"error": exc.to_dict()})
    except (TypeError, ValueError):
        return _invalid("kernel_push", auth, "KAGGLE_JOB_INVALID", "job must contain only JSON-serializable values")

    name = username or username_for(owner, account, auth)
    if not name:
        return envelope(
            "error",
            "kernel_push",
            auth,
            {"error": {"error_code": "KAGGLE_IDENTITY_UNKNOWN", "message": "could not determine the Kaggle username; run kaggle_auth_status with verify=true", "retryable": True}},
        )
    reference = f"{name}/{slug}"
    metadata = {
        "id": reference,
        "title": slug.replace("-", " ").title(),
        "code_file": "worker.py",
        "language": "python",
        "kernel_type": "script",
        "is_private": True,
        "enable_gpu": bool(gpu),
        "enable_internet": bool(internet),
        "dataset_sources": list(dict.fromkeys(dataset_sources)),
        "competition_sources": [],
        "kernel_sources": list(dict.fromkeys(qualify(item, name) for item in kernel_sources)),
        "model_sources": [],
    }
    acc = (accelerator or DEFAULT_ACCELERATOR) if gpu else None
    timeout = str(int(time_budget_seconds) + 240)
    digest = sha256_text(json.dumps({"code": composed, "metadata": metadata, "timeout": timeout, "acc": acc}, sort_keys=True))
    base = {"slug": reference, "source_sha256": source_digest}

    try:
        with locked(_ledger_path()):
            ledger = read_json(_ledger_path(), {})
            prior = ledger.get(key)
            if prior is not None:
                if prior.get("digest") != digest:
                    return envelope(
                        "rejected",
                        "kernel_push",
                        auth,
                        {**base, "error": {"error_code": "KAGGLE_IDEMPOTENCY_KEY_REUSED", "message": "this idempotency_key was already used for a different payload; use a new key"}},
                    )
                if prior.get("state") == "submitted":
                    return envelope("submitted", "kernel_push", auth, {**prior["receipt"], "replayed": True})
                if prior.get("state") == "submitting":
                    return envelope(
                        "unknown_delivery",
                        "kernel_push",
                        auth,
                        {**base, "error": {"error_code": "KAGGLE_DELIVERY_UNKNOWN", "message": "an earlier attempt with this key has no confirmed outcome; check kaggle_kernel_status before pushing again with a new key"}},
                    )
            ledger[key] = {"state": "submitting", "digest": digest, "slug": reference, "at": time.time()}
            write_json(_ledger_path(), ledger)
    except WorkspaceError as exc:
        return envelope("error", "kernel_push", auth, {"error": exc.to_dict()})

    arguments = {
        "code": composed,
        "code_file": "worker.py",
        "metadata": metadata,
        "timeout": timeout,
        "accelerator": acc,
    }
    outcome = "unknown_delivery"
    payload: dict[str, Any] = dict(base)
    try:
        results = backend_module.get_backend().run(
            [("kernel_push", arguments)], bearer_token=auth.bearer_token, timeout=300
        )
    except KaggleBackendError as exc:
        sent = exc.code in {"KAGGLE_RUNNER_TIMEOUT", "KAGGLE_RUNNER_PROTOCOL"}
        outcome = "unknown_delivery" if sent else "error"
        payload["error"] = exc.to_dict()
    else:
        result = results[0]
        if result.ok:
            data = result.data or {}
            invalid = data.get("invalid") or {}
            if data.get("error") or invalid:
                outcome = "rejected"
                payload["error"] = {
                    "error_code": "KAGGLE_PUSH_REJECTED",
                    "message": str(data.get("error") or "invalid input sources")[:400],
                    "invalid": invalid,
                }
            else:
                outcome = "submitted"
                payload.update({"url": data.get("url"), "version": data.get("version"), "replayed": False})
        elif result.status_code is not None and 400 <= int(result.status_code) < 500:
            outcome = "rejected"
            payload["error"] = {"error_code": "KAGGLE_PUSH_REJECTED", "message": str(result.error_message)[:400], "status_code": result.status_code}
        else:
            payload["error"] = {"error_code": "KAGGLE_DELIVERY_UNKNOWN", "message": str(result.error_message)[:400], "status_code": result.status_code}

    try:
        with locked(_ledger_path()):
            ledger = read_json(_ledger_path(), {})
            if outcome == "submitted":
                ledger[key] = {"state": "submitted", "digest": digest, "slug": reference, "receipt": payload, "at": time.time()}
            elif outcome in {"rejected", "error"}:
                ledger[key] = {"state": "rejected", "digest": digest, "slug": reference, "at": time.time()}
            write_json(_ledger_path(), ledger)
    except WorkspaceError:
        payload.setdefault("warnings", []).append("ledger update failed; do not replay this key")
    return envelope(outcome, "kernel_push", auth, payload)


def status(*, owner: str, slug: str, account: str = "default") -> KaggleOperationResult:
    auth = resolve_kaggle_auth(owner=owner, account=account)
    if not auth.authenticated:
        return envelope("auth_required", "kernel_status", auth)
    reference = slug.strip()
    if "/" not in reference:
        name = username_for(owner, account, auth)
        if not name:
            return envelope("error", "kernel_status", auth, {"error": {"error_code": "KAGGLE_IDENTITY_UNKNOWN", "message": "pass slug as owner/slug or verify authentication"}})
        reference = qualify(reference, name)
    _, results, failure = run_operations("kernel_status", owner, account, [("kernel_status", {"kernel": reference})])
    if failure is not None:
        return failure
    assert results is not None
    if not results[0].ok:
        return op_failure("kernel_status", auth, results[0])
    data = results[0].data or {}
    state = str(data.get("status", "UNKNOWN"))
    return envelope(
        "ok",
        "kernel_status",
        auth,
        {
            "slug": reference,
            "status": state,
            "terminal": state in TERMINAL_STATUSES,
            "succeeded": state == "COMPLETE",
            "failure_message": data.get("failure_message"),
        },
    )


def _decode_read(entry: dict[str, Any] | None, name: str) -> dict[str, Any] | None:
    if entry is None:
        return None
    text = entry.get("text", "")
    if name.endswith(".json") and not entry.get("truncated"):
        try:
            return {"json": json.loads(text), "bytes": entry.get("bytes")}
        except json.JSONDecodeError:
            pass
    return {"text": text, "truncated": bool(entry.get("truncated")), "bytes": entry.get("bytes")}


def output(
    *,
    owner: str,
    slug: str,
    account: str = "default",
    read: Sequence[str] = (),
    max_read_bytes: int = 16_384,
    log_tail_chars: int = 0,
    live_log_seconds: int = 0,
    page_token: str | None = None,
) -> KaggleOperationResult:
    auth = resolve_kaggle_auth(owner=owner, account=account)
    if not auth.authenticated:
        return envelope("auth_required", "kernel_output", auth)
    reference = slug.strip()
    if "/" not in reference:
        name = username_for(owner, account, auth)
        if not name:
            return envelope("error", "kernel_output", auth, {"error": {"error_code": "KAGGLE_IDENTITY_UNKNOWN", "message": "pass slug as owner/slug or verify authentication"}})
        reference = qualify(reference, name)
    wanted = list(dict.fromkeys(read))[:8]
    per_file = max(1, min(int(max_read_bytes), MAX_READ_TOTAL // max(1, len(wanted))))
    tail = max(0, min(int(log_tail_chars), 12_000))
    operations: list[tuple[str, dict[str, Any]]] = [
        (
            "kernel_output",
            {"kernel": reference, "read": wanted, "max_read_bytes": per_file, "log_tail_chars": tail if not live_log_seconds else 0, "page_token": page_token},
        )
    ]
    if live_log_seconds:
        operations.append(("kernel_logs", {"kernel": reference, "seconds": live_log_seconds, "log_tail_chars": tail or 4000}))
    _, results, failure = run_operations("kernel_output", owner, account, operations, timeout=max(120, int(live_log_seconds) + 60))
    if failure is not None:
        return failure
    assert results is not None
    if not results[0].ok:
        return op_failure("kernel_output", auth, results[0])
    data = results[0].data or {}
    payload: dict[str, Any] = {
        "slug": reference,
        "files": data.get("files", []),
        "has_more": bool(data.get("has_more")),
        "next_page_token": data.get("next_page_token"),
        "reads": {name: _decode_read((data.get("reads") or {}).get(name), name) for name in wanted},
    }
    if "log_tail" in data:
        payload["log_tail"] = data["log_tail"]
    warnings: tuple[str, ...] = ()
    if live_log_seconds:
        if results[1].ok:
            payload["log_tail"] = (results[1].data or {}).get("log_tail", "")
        else:
            warnings = ("live log unavailable: " + str(results[1].error_message),)
    return envelope("ok", "kernel_output", auth, payload, warnings)


__all__ = [
    "FAILED_STATUSES",
    "TERMINAL_STATUSES",
    "output",
    "push",
    "qualify",
    "reset_username_cache",
    "status",
    "username_for",
    "valid_slug",
]
