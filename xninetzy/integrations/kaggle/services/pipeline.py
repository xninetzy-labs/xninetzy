from __future__ import annotations

import json
import re
import time
from typing import Any

from xninetzy.integrations.kaggle import backend as backend_module
from xninetzy.integrations.kaggle.auth_adapter import resolve_kaggle_auth
from xninetzy.integrations.kaggle.backend import KaggleBackendError
from xninetzy.integrations.kaggle.services import kernels, pipeline_recovery
from xninetzy.integrations.kaggle.services.base import KaggleOperationResult, envelope
from xninetzy.integrations.kaggle.workspace import (
    DATASET_REF_PATTERN,
    NAME_PATTERN,
    WorkspaceError,
    locked,
    read_json,
    require_pattern,
    resolve_source_path,
    sha256_text,
    subdir,
    write_json,
)

ACTIVE_STATES = frozenset({"submitted", "submitting"})
ATTENTION_STATES = frozenset({"failed", "partial", "unknown_delivery"})
DEFERRAL_BACKOFF_CAP = 12
JOB_KEYS = frozenset(
    {
        "slug",
        "source_path",
        "source",
        "params",
        "depends_on",
        "kernel_sources",
        "dataset_sources",
        "accelerator",
        "internet",
        "time_budget_seconds",
        "max_attempts",
        "summary_required",
        "mount_dependencies",
        "adopt_run",
        "adopt_gpu",
    }
)
ACCELERATORS = frozenset({"none", "gpu", "gpu_or_cpu"})
MAX_JOBS = 200
MAX_JOB_SLUG = 45
MIN_GPU_SECONDS = 900
GPU_RESERVE_SECONDS = 300
SUBMITTING_GRACE_SECONDS = 120
TRANSIENT_MARKERS = ("maximum batch", "quota", "too many")


def _path(name: str):
    return subdir("pipelines") / f"{name}.json"


def _error(operation: str, auth, code: str, message: str, status: str = "invalid_input") -> KaggleOperationResult:
    return envelope(status, operation, auth, {"error": {"error_code": code, "message": message}})


def _int_in(value: Any, low: int, high: int, default: int, label: str) -> int:
    if value is None:
        return default
    if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
        raise WorkspaceError("KAGGLE_PIPELINE_INVALID", f"{label} must be an integer between {low} and {high}")
    return value


def _normalize_job(raw: Any, name: str) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise WorkspaceError("KAGGLE_PIPELINE_INVALID", "each job must be an object")
    unknown = set(raw) - JOB_KEYS
    if unknown:
        raise WorkspaceError("KAGGLE_PIPELINE_INVALID", "unknown job keys: " + ", ".join(sorted(unknown)))
    slug = str(raw.get("slug", "")).strip()
    if not kernels.valid_slug(slug) or len(slug) > MAX_JOB_SLUG:
        raise WorkspaceError("KAGGLE_SLUG_INVALID", f"job slug {slug!r} must be {kernels.MIN_SLUG}-{MAX_JOB_SLUG} characters of lowercase letters, digits and hyphens")
    accelerator = str(raw.get("accelerator", "none"))
    if accelerator not in ACCELERATORS:
        raise WorkspaceError("KAGGLE_PIPELINE_INVALID", "accelerator must be none, gpu or gpu_or_cpu")
    adopt_run = raw.get("adopt_run")
    if adopt_run is not None and (not isinstance(adopt_run, str) or not kernels.valid_slug(adopt_run)):
        raise WorkspaceError("KAGGLE_PIPELINE_INVALID", "adopt_run must be an existing kernel slug in the authenticated account")
    if not isinstance(raw.get("adopt_gpu", False), bool):
        raise WorkspaceError("KAGGLE_PIPELINE_INVALID", "adopt_gpu must be a boolean")
    source, source_path = raw.get("source"), raw.get("source_path")
    if bool(source) == bool(source_path):
        raise WorkspaceError("KAGGLE_SOURCE_REQUIRED", f"job {slug} needs exactly one of source or source_path")
    if source:
        target = subdir("pipelines", f"{name}.sources") / f"{slug}.py"
        target.write_text(str(source), encoding="utf-8")
        resolved = target
    else:
        resolved = resolve_source_path(str(source_path))
    params = raw.get("params") or {}
    if not isinstance(params, dict):
        raise WorkspaceError("KAGGLE_PIPELINE_INVALID", "params must be an object")
    try:
        json.dumps(params)
    except (TypeError, ValueError):
        raise WorkspaceError("KAGGLE_JOB_INVALID", "params must contain only JSON-serializable values") from None
    datasets = [str(item) for item in raw.get("dataset_sources") or []]
    for item in datasets:
        if not DATASET_REF_PATTERN.match(item):
            raise WorkspaceError("KAGGLE_DATASET_REF_INVALID", f"dataset source {item!r} must look like owner/dataset-slug")
    return {
        "slug": slug,
        "run_slug": slug,
        "state": "pending",
        "attempt": 1,
        "source_path": str(resolved),
        "source_sha256": sha256_text(resolved.read_text(encoding="utf-8")),
        "params": params,
        "depends_on": [str(item) for item in raw.get("depends_on") or []],
        "kernel_sources": [str(item) for item in raw.get("kernel_sources") or []],
        "dataset_sources": datasets,
        "accelerator": accelerator,
        "internet": bool(raw.get("internet", True)),
        "time_budget_seconds": _int_in(raw.get("time_budget_seconds"), 60, 43_200, 3600, "time_budget_seconds"),
        "max_attempts": _int_in(raw.get("max_attempts"), 1, 32, 1, "max_attempts"),
        "summary_required": bool(raw.get("summary_required", False)),
        "mount_dependencies": bool(raw.get("mount_dependencies", True)),
        "previous_sources": [],
        "stalled": 0,
        "last_progress": -1,
        "not_before": 0,
        "gpu": False,
        "adopt_run": adopt_run,
        "adopt_gpu": raw.get("adopt_gpu", False),
    }


def _check_graph(jobs: list[dict[str, Any]]) -> None:
    slugs = [job["slug"] for job in jobs]
    if len(set(slugs)) != len(slugs):
        raise WorkspaceError("KAGGLE_PIPELINE_INVALID", "job slugs must be unique")
    known = set(slugs)
    for job in jobs:
        missing = [dep for dep in job["depends_on"] if dep not in known or dep == job["slug"]]
        if missing:
            raise WorkspaceError("KAGGLE_PIPELINE_INVALID", f"job {job['slug']} has invalid dependencies: {missing}")
    remaining = {job["slug"]: set(job["depends_on"]) for job in jobs}
    while remaining:
        ready = [slug for slug, deps in remaining.items() if not deps]
        if not ready:
            raise WorkspaceError("KAGGLE_PIPELINE_INVALID", "dependency cycle detected among: " + ", ".join(sorted(remaining)))
        for slug in ready:
            remaining.pop(slug)
        for deps in remaining.values():
            deps.difference_update(ready)


def _counts(jobs: list[dict[str, Any]]) -> dict[str, int]:
    result: dict[str, int] = {}
    for job in jobs:
        result[job["state"]] = result.get(job["state"], 0) + 1
    return dict(sorted(result.items()))


def _view(job: dict[str, Any]) -> dict[str, Any]:
    view = {
        "slug": job["slug"],
        "run_slug": job["run_slug"],
        "state": job["state"],
        "attempt": job["attempt"],
        "accelerator": job["accelerator"],
        "gpu_used": job["gpu"],
        "depends_on": job["depends_on"],
    }
    for key in ("remote_status", "failure", "last_error"):
        if job.get(key):
            view[key] = str(job[key])[:300]
    if job.get("summary") is not None:
        view["summary"] = job["summary"]
    return view


def _digest(limits: dict[str, int], jobs: list[dict[str, Any]]) -> str:
    stable = [{key: job[key] for key in sorted(JOB_KEYS - {"source"}) if key in job} | {"source_sha256": job["source_sha256"]} for job in jobs]
    return sha256_text(json.dumps({"limits": limits, "jobs": stable}, sort_keys=True))


def _adopt_jobs(jobs: list[dict[str, Any]], owner: str, account: str, auth) -> str | None:
    adopted = [job for job in jobs if job.get("adopt_run")]
    if not adopted:
        return None
    user = kernels.username_for(owner, account, auth)
    if not user:
        raise WorkspaceError("KAGGLE_IDENTITY_UNKNOWN", "could not verify the Kaggle account for adoption")
    backend = backend_module.get_backend()
    responses = backend.run(
        [("kernel_status", {"kernel": f"{user}/{job['adopt_run']}"}) for job in adopted],
        bearer_token=auth.bearer_token,
    )
    complete = []
    now = time.time()
    for job, response in zip(adopted, responses, strict=True):
        if not response.ok:
            raise WorkspaceError("KAGGLE_ADOPTION_UNVERIFIED", f"could not verify existing run {job['adopt_run']}; no replacement was submitted")
        run = job["adopt_run"]
        remote = str((response.data or {}).get("status", "UNKNOWN")).upper()
        job.update(run_slug=run, gpu=job["adopt_gpu"], remote_status=remote)
        match = re.fullmatch(re.escape(job["slug"]) + r"-r([1-9]\d*)", run)
        job["attempt"] = int(match.group(1)) if match else 1
        job["adopted_at"] = now
        if remote == "COMPLETE":
            complete.append(job)
        elif remote in kernels.FAILED_STATUSES:
            job["state"] = "failed"
            job["failure"] = (response.data or {}).get("failure_message") or remote
        elif remote in {"RUNNING", "QUEUED", "NEW_SCRIPT"}:
            job["state"] = "submitted"
        else:
            raise WorkspaceError("KAGGLE_ADOPTION_UNVERIFIED", f"existing run {run} has unresolved status {remote}")
    if complete:
        outputs = backend.run([
            ("kernel_output", {"kernel": f"{user}/{job['run_slug']}", "read": ["summary.json"], "max_read_bytes": 65_536})
            for job in complete
        ], bearer_token=auth.bearer_token)
        for job, output in zip(complete, outputs, strict=True):
            if not output.ok:
                raise WorkspaceError("KAGGLE_ADOPTION_UNVERIFIED", f"could not verify output of {job['run_slug']}")
            entry = ((output.data or {}).get("reads") or {}).get("summary.json")
            summary = None
            if entry and not entry.get("truncated"):
                try:
                    summary = json.loads(entry.get("text", ""))
                except json.JSONDecodeError:
                    pass
            _apply_completion(job, summary, now)
    return user


def plan(
    *,
    owner: str,
    name: str,
    jobs: list[dict[str, Any]],
    account: str = "default",
    limits: dict[str, int] | None = None,
    replace: bool = False,
) -> KaggleOperationResult:
    auth = resolve_kaggle_auth(owner=owner, account=account)
    try:
        label = require_pattern(name, NAME_PATTERN, "KAGGLE_PIPELINE_NAME_INVALID", "pipeline name")
        if not isinstance(jobs, list) or not 1 <= len(jobs) <= MAX_JOBS:
            raise WorkspaceError("KAGGLE_PIPELINE_INVALID", f"jobs must be a list of 1-{MAX_JOBS} objects")
        limit_values = limits or {}
        if not isinstance(limit_values, dict):
            raise WorkspaceError("KAGGLE_PIPELINE_INVALID", "limits must be an object")
        resolved_limits = {
            "cpu": _int_in(limit_values.get("cpu"), 1, 5, 4, "limits.cpu"),
            "gpu": _int_in(limit_values.get("gpu"), 0, 2, 1, "limits.gpu"),
        }
        normalized = [_normalize_job(raw, label) for raw in jobs]
        _check_graph(normalized)
        spec_digest = _digest(resolved_limits, normalized)
        path = _path(label)
        with locked(path):
            existing = read_json(path, None)
            if existing is not None:
                if existing.get("spec_digest") == spec_digest:
                    return envelope("unchanged", "pipeline_plan", auth, _plan_payload(existing))
                started = any(job["state"] != "pending" or job["attempt"] > 1 for job in existing["jobs"])
                if started:
                    raise WorkspaceError("KAGGLE_PIPELINE_ACTIVE", "this pipeline already submitted work; plan a new name instead of replacing it")
                if not replace:
                    raise WorkspaceError("KAGGLE_PIPELINE_EXISTS", "a pipeline with this name exists; pass replace=true to overwrite its unstarted plan")
            adopted_user = _adopt_jobs(normalized, owner, account, auth)
            state = {
                "name": label,
                "created": time.time(),
                "spec_digest": spec_digest,
                "limits": resolved_limits,
                "kaggle_user": adopted_user,
                "cpu_not_before": 0,
                "gpu_not_before": 0,
                "jobs": normalized,
            }
            write_json(path, state)
    except (WorkspaceError, KaggleBackendError) as exc:
        return envelope("invalid_input", "pipeline_plan", auth, {"error": exc.to_dict()})
    return envelope("planned", "pipeline_plan", auth, _plan_payload(state))


def _plan_payload(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "pipeline": state["name"],
        "limits": state["limits"],
        "jobs": [_view(job) for job in state["jobs"]],
        "counts": _counts(state["jobs"]),
        "next_step": "kaggle_pipeline_tick",
    }


def status(*, owner: str, name: str = "", account: str = "default") -> KaggleOperationResult:
    auth = resolve_kaggle_auth(owner=owner, account=account)
    if not name:
        directory = subdir("pipelines")
        listing = []
        for path in sorted(directory.glob("*.json")):
            state = read_json(path, None)
            if state:
                listing.append({"pipeline": state["name"], "counts": _counts(state["jobs"])})
        return envelope("ok", "pipeline_status", auth, {"pipelines": listing})
    try:
        label = require_pattern(name, NAME_PATTERN, "KAGGLE_PIPELINE_NAME_INVALID", "pipeline name")
    except WorkspaceError as exc:
        return envelope("invalid_input", "pipeline_status", auth, {"error": exc.to_dict()})
    state = read_json(_path(label), None)
    if state is None:
        return _error("pipeline_status", auth, "KAGGLE_PIPELINE_NOT_FOUND", "no such pipeline", "not_found")
    return envelope("ok", "pipeline_status", auth, _tick_payload(state, [], []))


def _tick_payload(state: dict[str, Any], submitted: list[str], finished: list[str]) -> dict[str, Any]:
    jobs = state["jobs"]
    counts = _counts(jobs)
    by_slug = {job["slug"]: job for job in jobs}
    now = time.time()
    active = [job for job in jobs if job["state"] in ACTIVE_STATES]
    ready = [
        job
        for job in jobs
        if job["state"] == "pending" and all(by_slug[dep]["state"] == "complete" for dep in job["depends_on"])
    ]
    attention = [_view(job) for job in jobs if job["state"] in ATTENTION_STATES]
    done = all(job["state"] == "complete" for job in jobs)
    next_seconds: int | None = None
    if active:
        next_seconds = 60
    elif ready:
        next_seconds = int(max(60, min(job["not_before"] for job in ready) - now))
    return {
        "pipeline": state["name"],
        "counts": counts,
        "submitted": submitted,
        "finished": finished,
        "needs_attention": attention,
        "done": done,
        "blocked": not done and not active and not ready,
        "next_tick_seconds": next_seconds,
        "jobs": [_view(job) for job in jobs],
    }


def _bounded(summary: Any) -> Any:
    try:
        encoded = json.dumps(summary)
    except (TypeError, ValueError):
        return {"unserializable": True}
    if len(encoded) <= 6000:
        return summary
    return {"truncated": True, "keys": sorted(summary)[:40] if isinstance(summary, dict) else []}


def _number(value: Any) -> float:
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else 0.0


def _apply_completion(
    job: dict[str, Any],
    summary: Any,
    now: float,
    by_slug: dict[str, dict[str, Any]] | None = None,
    full: Any = None,
    details: dict[str, Any] | None = None,
) -> None:
    if not isinstance(summary, dict):
        if job["summary_required"]:
            job["state"] = "partial"
            job["failure"] = "summary.json missing, unreadable or not an object"
        else:
            job["state"] = "complete"
        job["summary"] = None
        return
    job["summary"] = _bounded(summary)
    flag = summary.get("complete")
    if flag is True or (flag is None and not job["summary_required"]):
        job["state"] = "complete"
        return
    unavailable, unextractable = pipeline_recovery.waiver_flags(job)
    if unavailable or unextractable:
        waived = pipeline_recovery.permanent_failures(
            full if full is not None else summary,
            pipeline_recovery.inherited_waivers(job, by_slug or {}),
            unavailable,
            unextractable,
            details,
        )
        if waived is not None:
            job["state"], job["waived"] = "complete", waived
            return
    progress = _number(summary.get("progress", 0))
    advanced = progress > job["last_progress"]
    deferred = summary.get("deferred")
    if isinstance(deferred, dict):
        job["deferrals"] = 0 if advanced else job.get("deferrals", 0) + 1
        delay = max(0.0, _number(deferred.get("retry_after_seconds", 1800)))
        job["not_before"] = now + delay * min(2 ** max(job["deferrals"] - 1, 0), DEFERRAL_BACKOFF_CAP)
        stalled = 0
    else:
        job["deferrals"] = 0
        stalled = 0 if advanced else job["stalled"] + 1
    job["stalled"], job["last_progress"] = stalled, progress
    if stalled < 2 and job["attempt"] < job["max_attempts"]:
        job["previous_sources"] = [job["run_slug"]]
        job["attempt"] += 1
        job["run_slug"] = f"{job['slug']}-r{job['attempt']}"
        job["state"] = "pending"
        job["gpu"] = False
    else:
        job["state"] = "partial"
        job["failure"] = "incomplete after " + str(job["attempt"]) + " attempt(s) without further progress"


def _reconcile(state: dict[str, Any], user: str, auth_token: str | None, now: float, finished: list[str]) -> None:
    active = [job for job in state["jobs"] if job["state"] in ACTIVE_STATES]
    if not active:
        return
    backend = backend_module.get_backend()
    statuses = backend.run(
        [("kernel_status", {"kernel": f"{user}/{job['run_slug']}"}) for job in active],
        bearer_token=auth_token,
    )
    completed: list[dict[str, Any]] = []
    for job, result in zip(active, statuses):
        if not result.ok:
            missing = result.status_code in (403, 404)
            if job["state"] == "submitting" and missing and now - job.get("submitting_at", now) > SUBMITTING_GRACE_SECONDS:
                job["state"] = "unknown_delivery"
                job["failure"] = "push outcome unknown and the kernel was not found; reconcile manually, never replay blindly"
            else:
                job["last_error"] = result.error_message
            continue
        remote = str((result.data or {}).get("status", "UNKNOWN"))
        job["remote_status"] = remote
        job.pop("last_error", None)
        if job["state"] == "submitting":
            job["state"] = "submitted"
        if remote == "COMPLETE":
            completed.append(job)
        elif remote in kernels.FAILED_STATUSES:
            job["state"] = "failed"
            job["failure"] = (result.data or {}).get("failure_message") or remote
            finished.append(job["run_slug"])
    if not completed:
        return
    outputs = backend.run(
        [
            ("kernel_output", {"kernel": f"{user}/{job['run_slug']}", "read": ["summary.json"], "max_read_bytes": 65_536})
            for job in completed
        ],
        bearer_token=auth_token,
    )
    for job, result in zip(completed, outputs):
        if not result.ok:
            job["last_error"] = result.error_message
            continue
        entry = ((result.data or {}).get("reads") or {}).get("summary.json")
        summary = None
        if entry and not entry.get("truncated"):
            try:
                summary = json.loads(entry.get("text", ""))
            except json.JSONDecodeError:
                summary = None
        full, details = summary, {}
        if isinstance(summary, dict) and any(pipeline_recovery.waiver_flags(job)) and summary.get("failures"):
            full, details = pipeline_recovery.resolve_failures(summary, backend, user, auth_token, job["run_slug"])
        _apply_completion(job, summary, now, {item["slug"]: item for item in state["jobs"]}, full, details)
        finished.append(job["run_slug"])


def _sources(job: dict[str, Any], by_slug: dict[str, dict[str, Any]], user: str) -> list[str]:
    dependencies = (
        [f"{user}/{by_slug[dep]['run_slug']}" for dep in job["depends_on"]] if job["mount_dependencies"] else []
    )
    previous = [f"{user}/{item}" for item in job["previous_sources"]]
    explicit = [kernels.qualify(item, user) for item in job["kernel_sources"]]
    return list(dict.fromkeys(dependencies + explicit + previous))


def _submit_ready(
    state: dict[str, Any],
    owner: str,
    account: str,
    user: str,
    auth_token: str | None,
    now: float,
    submitted: list[str],
    path,
) -> None:
    jobs = state["jobs"]
    by_slug = {job["slug"]: job for job in jobs}
    limits = state["limits"]
    active_cpu = sum(job["state"] in ACTIVE_STATES and not job["gpu"] for job in jobs)
    active_gpu = sum(job["state"] in ACTIVE_STATES and job["gpu"] for job in jobs)
    ready = [
        job
        for job in jobs
        if job["state"] == "pending"
        and now >= job["not_before"]
        and all(by_slug[dep]["state"] == "complete" for dep in job["depends_on"])
    ]
    ready.sort(key=lambda job: job.get("queue_rank", 0))
    remaining_gpu = 0
    wants_gpu = any(job["accelerator"] != "none" for job in ready)
    if wants_gpu and limits["gpu"] > active_gpu and now >= state["gpu_not_before"]:
        quota = backend_module.get_backend().run([("quota", {})], bearer_token=auth_token)[0]
        gpu = ((quota.data or {}).get("gpu") or {}) if quota.ok else {}
        remaining_gpu = int(gpu.get("remaining_seconds") or 0)
    for job in ready:
        wants = job["accelerator"] in {"gpu", "gpu_or_cpu"}
        use_gpu = bool(wants and remaining_gpu >= MIN_GPU_SECONDS and active_gpu < limits["gpu"] and now >= state["gpu_not_before"])
        if wants and not use_gpu and job["accelerator"] == "gpu":
            continue
        if not use_gpu and (now < state["cpu_not_before"] or active_cpu >= limits["cpu"]):
            continue
        budget = job["time_budget_seconds"]
        if use_gpu:
            budget = max(60, min(budget, remaining_gpu - GPU_RESERVE_SECONDS))
        job["state"], job["gpu"], job["submitting_at"] = "submitting", use_gpu, now
        write_json(path, state)
        outcome = kernels.push(
            owner=owner,
            account=account,
            slug=job["run_slug"],
            idempotency_key=f"pipeline:{state['name']}:{job['run_slug']}",
            source_path=job["source_path"],
            job={
                **job["params"],
                "_pipeline": state["name"],
                "_slug": job["slug"],
                "_attempt": job["attempt"],
                "_previous": job["previous_sources"],
            },
            gpu=use_gpu,
            internet=job["internet"],
            dataset_sources=job["dataset_sources"],
            kernel_sources=_sources(job, by_slug, user),
            time_budget_seconds=budget,
            username=user,
        )
        payload = outcome.payload or {}
        if outcome.status == "submitted":
            job["state"], job["receipt"], job["submitted_at"] = "submitted", payload, now
            job.pop("rejection", None)
            submitted.append(job["run_slug"])
            active_gpu += int(use_gpu)
            active_cpu += int(not use_gpu)
            remaining_gpu -= (budget + 240) if use_gpu else 0
        elif outcome.status == "unknown_delivery":
            job["state"] = "unknown_delivery"
            job["failure"] = str((payload.get("error") or {}).get("message", "delivery unknown"))[:300]
        elif outcome.status == "rejected":
            reason = str((payload.get("error") or {}).get("message", "rejected"))
            job["rejection"] = {"reason": reason[:300], "at": now}
            transient = any(marker in reason.lower() for marker in TRANSIENT_MARKERS)
            job["state"], job["gpu"] = ("pending", False) if transient else ("failed", False)
            if not transient:
                job["failure"] = reason[:300]
            if use_gpu:
                remaining_gpu = 0
                state["gpu_not_before"] = now + 300
            else:
                state["cpu_not_before"] = now + 60
                write_json(path, state)
                break
        else:
            job["state"], job["gpu"] = "pending", False
            job["last_error"] = str((payload.get("error") or {}).get("message", outcome.status))[:300]
            write_json(path, state)
            break
        write_json(path, state)


def tick(
    *,
    owner: str,
    name: str,
    idempotency_key: str,
    account: str = "default",
    reconcile_jobs: list[str] | None = None,
    restart_cancelled: list[str] | None = None,
    resume_partial: list[str] | None = None,
    accept_unavailable: list[str] | None = None,
    accept_unextractable: list[str] | None = None,
    requeue_back: list[str] | None = None,
) -> KaggleOperationResult:
    auth = resolve_kaggle_auth(owner=owner, account=account)
    if not auth.authenticated:
        return envelope("auth_required", "pipeline_tick", auth)
    try:
        label = require_pattern(name, NAME_PATTERN, "KAGGLE_PIPELINE_NAME_INVALID", "pipeline name")
    except WorkspaceError as exc:
        return envelope("invalid_input", "pipeline_tick", auth, {"error": exc.to_dict()})
    key = idempotency_key.strip()
    if not key:
        return _error("pipeline_tick", auth, "KAGGLE_IDEMPOTENCY_KEY_REQUIRED", "idempotency_key is required")
    path = _path(label)
    try:
        with locked(path):
            state = read_json(path, None)
            if state is None:
                return _error("pipeline_tick", auth, "KAGGLE_PIPELINE_NOT_FOUND", "no such pipeline; call kaggle_pipeline_plan first", "not_found")
            try:
                groups, recovery_digest, prior = pipeline_recovery.request(
                    state, key, reconcile_jobs, restart_cancelled, resume_partial, accept_unavailable,
                    accept_unextractable, requeue_back
                )
            except WorkspaceError as exc:
                return envelope("invalid_input", "pipeline_tick", auth, {"error": exc.to_dict()})
            if prior is not None:
                return envelope("ok", "pipeline_tick", auth, {**_tick_payload(state, [], []), "recovery": prior["audit"], "replayed": True})
            if state.get("last_tick_key") == key and "last_tick_result" in state:
                return envelope("ok", "pipeline_tick", auth, {**state["last_tick_result"], "replayed": True})
            user = state.get("kaggle_user") or kernels.username_for(owner, account, auth)
            if not user:
                return _error("pipeline_tick", auth, "KAGGLE_IDENTITY_UNKNOWN", "could not determine the Kaggle username", "error")
            state["kaggle_user"] = user
            now = time.time()
            submitted: list[str] = []
            finished: list[str] = []
            try:
                if any(groups):
                    audit = pipeline_recovery.recover(state, user, auth.bearer_token, now, groups)
                    state.setdefault("recovery_requests", {})[key] = {"digest": recovery_digest, "audit": audit, "at": now}
                    write_json(path, state)
                _reconcile(state, user, auth.bearer_token, now, finished)
                write_json(path, state)
                _submit_ready(state, owner, account, user, auth.bearer_token, now, submitted, path)
            except KaggleBackendError as exc:
                write_json(path, state)
                return envelope("error", "pipeline_tick", auth, {"pipeline": label, "error": exc.to_dict(), "counts": _counts(state["jobs"])})
            result = _tick_payload(state, submitted, finished)
            if any(groups):
                result["recovery"] = state["recovery_requests"][key]["audit"]
            state["last_tick_key"], state["last_tick_result"] = key, result
            write_json(path, state)
            if result["done"] or result["blocked"]:
                write_json(path.with_suffix(".terminal.json"), {
                    "pipeline": label, "done": result["done"], "blocked": result["blocked"],
                    "counts": result["counts"], "at": time.time(),
                })
            elif any(groups):
                path.with_suffix(".terminal.json").unlink(missing_ok=True)
    except WorkspaceError as exc:
        return envelope("error", "pipeline_tick", auth, {"error": exc.to_dict()})
    return envelope("ok", "pipeline_tick", auth, {**result, "replayed": False})


__all__ = ["plan", "status", "tick"]
