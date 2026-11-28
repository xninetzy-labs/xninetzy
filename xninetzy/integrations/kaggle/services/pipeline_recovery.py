from __future__ import annotations

import json
from typing import Any

from xninetzy.integrations.kaggle import backend as backend_module
from xninetzy.integrations.kaggle.workspace import WorkspaceError, sha256_text

CANCELLED = frozenset({"CANCELLED", "CANCELED", "CANCEL_ACKNOWLEDGED"})
ACTIVE = frozenset({"QUEUED", "RUNNING", "INITIALIZING"})
QUOTA_MARKER = "Drive verification"
PERMANENT_DOWNLOAD_ERRORS = ("zero_page_pdf", "404 Client Error")
UNAVAILABLE_SOURCE_ERROR = "Source file was not downloaded successfully"
QUALITY_REFUSALS = (
    "Image page has unresolved OCR quality",
    "Unresolved character corruption",
    "Partial/failed document conversion",
)
ARMABLE_STATES = frozenset({"pending", "submitted", "partial"})
MANIFESTS = {"extract": ("results.json", "status"), "download": ("downloads.json", "download_status")}
MANIFEST_READ_BYTES = 1_048_576
DETAIL_FIELDS = {"name": ("name",), "company": ("nama_perusahaan",), "sector": ("sector",), "year": ("tahun", "folder_year")}
DEFAULT_RETRY_AFTER_SECONDS = 1800.0
BACK_OF_QUEUE = 1
CLEARED_FIELDS = ("failure", "last_error", "remote_status", "receipt", "rejection")


def request(state, key, reconcile_jobs, restart_cancelled, resume_partial=None, accept_unavailable=None,
            accept_unextractable=None, requeue_back=None):
    groups = []
    slugs = {job["slug"] for job in state["jobs"]}
    for values in (reconcile_jobs, restart_cancelled, resume_partial, accept_unavailable, accept_unextractable,
                   requeue_back):
        values = [] if values is None else values
        if (not isinstance(values, list) or len(values) > 20
                or any(not isinstance(value, str) or value not in slugs for value in values)
                or len(set(values)) != len(values)):
            raise WorkspaceError("KAGGLE_RECOVERY_INVALID", "recovery lists require up to 20 unique existing job slugs")
        groups.append(sorted(values))
    flat = [slug for group in groups for slug in group]
    if len(flat) != len(set(flat)):
        raise WorkspaceError("KAGGLE_RECOVERY_INVALID", "a job may appear in only one recovery list")
    if groups[5]:
        payload = groups
    elif groups[4]:
        payload = groups[:5]
    elif groups[2] or groups[3]:
        payload = groups[:4]
    else:
        payload = groups[:2]
    digest = sha256_text(json.dumps(payload))
    prior = state.get("recovery_requests", {}).get(key)
    if prior is not None and prior["digest"] != digest:
        raise WorkspaceError("KAGGLE_RECOVERY_KEY_REUSED", "this recovery key is bound to a different request")
    return groups, digest, prior


def _missing(result):
    return (result.status_code in (403, 404)
            or result.error_type == "ValueError" and "Cannot access kernel" in (result.error_message or ""))


def recover(state: dict[str, Any], user: str, token, now, groups):
    backend = backend_module.get_backend()
    back = set(groups[5])
    selected = set(groups[0] + groups[1]) | back
    resumed = set(groups[2])
    jobs = [job for job in state["jobs"] if job["slug"] in selected]
    resuming = [job for job in state["jobs"] if job["slug"] in resumed]
    probed = jobs + resuming
    statuses = backend.run([("kernel_status", {"kernel": f"{user}/{job['run_slug']}"}) for job in probed], bearer_token=token)
    witness = next((f"{user}/{job['run_slug']}" for job in state["jobs"]
                    if job["state"] == "complete" and job["slug"] not in selected | resumed), None)
    presence = {}
    if witness:
        refs = [f"{user}/{slug}" for job in probed
                for slug in (job["run_slug"], f"{job['slug']}-r{job['attempt'] + 1}")]
        result = backend.run([("kernel_presence", {"kernels": refs, "witness": witness})], bearer_token=token)[0]
        if result.ok:
            presence = result.data or {}
    verified_list = (presence.get("username") == user and presence.get("complete") is True
                     and presence.get("witness_present") is True)
    found = set(presence.get("found") or [])
    redacted = presence.get("redacted", 0)
    if isinstance(redacted, bool) or not isinstance(redacted, int) or redacted < 0:
        verified_list, redacted = False, 0
    exact_list = verified_list and redacted == 0
    unused = _unused_slugs(backend, token, user, jobs) if verified_list and redacted else {}
    audit = []
    for job, result in zip(jobs, statuses):
        old = job["run_slug"]
        entry = {"slug": job["slug"], "from": old, "at": now, "outcome": "unresolved"}
        audit.append(entry)
        remote = str((result.data or {}).get("status", "UNKNOWN")) if result.ok else None
        entry["remote_status"] = remote
        if remote in ACTIVE or remote == "COMPLETE":
            job["state"], job["remote_status"] = "submitted", remote
            job.pop("failure", None)
            entry["outcome"] = "adopted_existing"
            continue
        to_back = job["slug"] in back
        uncertain = (job["slug"] in groups[0] or to_back) and job["state"] == "unknown_delivery"
        cancelled = job["slug"] in groups[1] and remote in CANCELLED and exact_list
        absence = (uncertain and not result.ok and _missing(result) and verified_list
                   and f"{user}/{old}" not in found
                   and now - job.get("submitting_at", now) > 120
                   and (exact_list or _never_connected(job) or to_back))
        new = f"{job['slug']}-r{job['attempt'] + 1}"
        if redacted:
            entry["redacted_listing_rows"] = redacted
        if not (absence or cancelled):
            entry["reason"] = "remote state or owned-list evidence does not authorize a new attempt"
            continue
        if (not verified_list or f"{user}/{new}" in found or job["attempt"] >= job["max_attempts"]
                or not exact_list and not unused.get(f"{user}/{new}")):
            entry["reason"] = "new attempt requires a verified unused slug and remaining attempts"
            continue
        previous = list(job["previous_sources"])
        if cancelled:
            output = backend.run([("kernel_output", {"kernel": f"{user}/{old}", "read": []})], bearer_token=token)[0]
            if not output.ok:
                entry["reason"] = "cancelled checkpoint inventory could not be verified"
                continue
            if (output.data or {}).get("files"):
                previous.append(old)
        job.update(state="pending", run_slug=new, attempt=job["attempt"] + 1,
                   gpu=False, not_before=now, previous_sources=list(dict.fromkeys(previous)))
        for field in CLEARED_FIELDS:
            job.pop(field, None)
        reason = "verified_cancelled" if cancelled else "verified_non_delivery"
        if exact_list:
            final_reason = reason
        elif to_back and not _never_connected(job):
            final_reason = "owner_accepted_redacted_listing_risk"
        else:
            final_reason = "verified_non_delivery_before_connection"
        if to_back:
            job["queue_rank"] = BACK_OF_QUEUE
            entry["queued_at_back"] = True
        entry.update(outcome="queued_continuation", to=new, reason=final_reason,
                     previous_sources=job["previous_sources"], owned_kernels_scanned=presence.get("scanned"))
    audit.extend(_resume(resuming, statuses[len(jobs):], user, exact_list, found, now))
    by_slug = {job["slug"]: job for job in state["jobs"]}
    def resolve(summary, run_slug):
        return resolve_failures(summary, backend, user, token, run_slug)

    audit.extend(_waive([by_slug[slug] for slug in groups[3]], by_slug, now, "waive_unavailable", resolve))
    audit.extend(_waive([by_slug[slug] for slug in groups[4]], by_slug, now, "waive_unextractable", resolve))
    return audit


def _never_connected(job):
    failure = str(job.get("failure") or "")
    return "NameResolutionError" in failure and "Failed to resolve" in failure


def _unused_slugs(backend, token, user, jobs):
    names = [f"{user}/{job['slug']}-r{job['attempt'] + 1}" for job in jobs]
    if not names:
        return {}
    results = backend.run([("kernel_status", {"kernel": name}) for name in names], bearer_token=token)
    return {name: not result.ok and _missing(result) for name, result in zip(names, results)}


def _quota_limited(summary):
    if not isinstance(summary, dict):
        return False
    failures = summary.get("failures")
    listed = [item.get("error") for item in failures if isinstance(item, dict)] if isinstance(failures, list) else []
    return isinstance(summary.get("deferred"), dict) or any(QUOTA_MARKER in str(error) for error in listed)


def _retry_after(summary):
    deferred = summary.get("deferred")
    value = deferred.get("retry_after_seconds") if isinstance(deferred, dict) else None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return DEFAULT_RETRY_AFTER_SECONDS
    return max(0.0, float(value))


def _resume(jobs, results, user, verified_list, found, now):
    audit = []
    for job, result in zip(jobs, results):
        old = job["run_slug"]
        remote = str((result.data or {}).get("status", "UNKNOWN")) if result.ok else None
        entry = {"slug": job["slug"], "from": old, "at": now, "outcome": "unresolved", "remote_status": remote}
        audit.append(entry)
        if job["state"] != "partial" or remote != "COMPLETE" or not _quota_limited(job.get("summary")):
            entry["reason"] = "only a finished partial run stopped by a Drive quota may be resumed"
            continue
        new = f"{job['slug']}-r{job['attempt'] + 1}"
        if not verified_list or f"{user}/{new}" in found or job["attempt"] >= job["max_attempts"]:
            entry["reason"] = "new attempt requires a verified unused slug and remaining attempts"
            continue
        not_before = now + _retry_after(job["summary"])
        job.update(state="pending", run_slug=new, attempt=job["attempt"] + 1, gpu=False, stalled=0,
                   not_before=not_before, previous_sources=[old])
        for field in CLEARED_FIELDS:
            job.pop(field, None)
        entry.update(outcome="queued_continuation", to=new, reason="verified_quota_deferral",
                     previous_sources=[old], not_before=not_before)
    return audit


def inherited_waivers(job, by_slug):
    ids = set()
    for dependency in job["depends_on"]:
        for item in (by_slug.get(dependency) or {}).get("waived") or []:
            ids.add(item.get("id"))
    return ids


def _counted(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _extract_failure_permitted(item, inherited, unavailable, unextractable):
    error = str(item.get("error", ""))
    if error == UNAVAILABLE_SOURCE_ERROR:
        return (unavailable or unextractable) and item.get("id") in inherited
    return unextractable and error.startswith(QUALITY_REFUSALS)


def _details(item):
    found = {}
    for key, sources in DETAIL_FIELDS.items():
        value = next((item[source] for source in sources if item.get(source) is not None), None)
        if value is not None:
            found[key] = value
    return found


def resolve_failures(summary, backend, user, token, run_slug):
    if not isinstance(summary, dict) or not isinstance(summary.get("failures"), list):
        return summary, {}
    manifest = MANIFESTS.get(summary.get("mode"))
    if manifest is None:
        return summary, {}
    name, status_key = manifest
    result = backend.run([("kernel_output", {"kernel": f"{user}/{run_slug}", "read": [name], "max_read_bytes": MANIFEST_READ_BYTES})],
                         bearer_token=token)[0]
    entry = ((result.data or {}).get("reads") or {}).get(name) if result.ok else None
    if not isinstance(entry, dict) or entry.get("truncated"):
        return summary, {}
    try:
        records = json.loads(entry.get("text", ""))["records"]
    except (ValueError, KeyError, TypeError):
        return summary, {}
    if not isinstance(records, list):
        return summary, {}
    failed = [item for item in records if isinstance(item, dict) and item.get(status_key) == "failed"]
    full = [{"id": item.get("id"), "error": item.get("error")} for item in failed]
    if full[:len(summary["failures"])] != summary["failures"]:
        return summary, {}
    details = {item.get("id"): _details(item) for item in failed}
    return {**summary, "failures": full}, details


def permanent_failures(summary, inherited, unavailable=True, unextractable=False, details=None):
    if not isinstance(summary, dict) or summary.get("deferred"):
        return None
    failures = summary.get("failures")
    if not isinstance(failures, list) or not failures or any(not isinstance(item, dict) for item in failures):
        return None
    mode = summary.get("mode")
    if mode == "download":
        accounted = (_counted(summary.get("downloaded")) and _counted(summary.get("expected"))
                     and summary["downloaded"] + len(failures) == summary["expected"])
        permitted = unavailable and all(str(item.get("error", "")).startswith(PERMANENT_DOWNLOAD_ERRORS) for item in failures)
    elif mode == "extract":
        accounted = (_counted(summary.get("processed")) and summary.get("processed") == summary.get("expected")
                     and not summary.get("partial") and summary.get("failed") == len(failures))
        permitted = all(_extract_failure_permitted(item, inherited, unavailable, unextractable) for item in failures)
    else:
        return None
    if not accounted or not permitted:
        return None
    return [{"id": item.get("id"), "error": str(item.get("error"))[:120], **(details or {}).get(item.get("id"), {})}
            for item in failures]


def waiver_flags(job):
    return bool(job.get("waive_unavailable")), bool(job.get("waive_unextractable"))


def _truncated(summary):
    failures = summary.get("failures") if isinstance(summary, dict) else None
    failed = summary.get("failed") if isinstance(summary, dict) else None
    return isinstance(failures, list) and _counted(failed) and failed > len(failures)


def _waive(jobs, by_slug, now, flag, resolve):
    audit = []
    for job in jobs:
        entry = {"slug": job["slug"], "from": job["run_slug"], "at": now, "outcome": "unresolved"}
        audit.append(entry)
        if job["state"] not in ARMABLE_STATES:
            entry["reason"] = "only a pending, running or partial job may be armed to waive files"
            continue
        job[flag] = True
        waived = None
        if job["state"] == "partial":
            unavailable, unextractable = waiver_flags(job)
            summary, details = resolve(job["summary"], job["run_slug"])
            waived = permanent_failures(summary, inherited_waivers(job, by_slug), unavailable, unextractable, details)
        if waived is None:
            reason = "failure list is truncated, so not every failed file can be verified" if _truncated(job.get("summary")) \
                else "waived automatically once every failed file is permanently unavailable or unextractable"
            entry.update(outcome="armed", reason=reason)
            continue
        job["state"], job["waived"] = "complete", waived
        job.pop("failure", None)
        entry.update(outcome="waived_unavailable", waived=waived)
    return audit
