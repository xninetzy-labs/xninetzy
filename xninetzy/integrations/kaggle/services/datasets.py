from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

from xninetzy.integrations.kaggle.auth_adapter import resolve_kaggle_auth
from xninetzy.integrations.kaggle.services.base import (
    KaggleOperationResult,
    envelope,
    op_failure,
    run_operations,
)
from xninetzy.integrations.kaggle.workspace import (
    DATASET_REF_PATTERN,
    NAME_PATTERN,
    WorkspaceError,
    locked,
    read_json,
    require_pattern,
    subdir,
    workspace_dir,
    write_json,
)
from xninetzy.os.research.sources.kaggle import KaggleAdapter
from xninetzy.os.research.sources.registry import get_adapter

OPERATIONS = [
    "search",
    "get",
    "validate",
    "register",
    "download",
    "kernel_push",
    "kernel_status",
    "kernel_output",
    "pipeline_plan",
    "pipeline_status",
    "pipeline_tick",
]
DEFAULT_MAX_BYTES = 2_147_483_648
_RESULTS_CACHE: dict[str, KaggleOperationResult] = {}


def reset_cache() -> None:
    _RESULTS_CACHE.clear()


def _adapter_registered() -> bool:
    try:
        from xninetzy.os.research.sources.registry import list_adapters

        return any(a.id == "kaggle" for a in list_adapters())
    except Exception:
        return False


def _env_credentials_present() -> bool:
    return bool(os.environ.get("KAGGLE_USERNAME")) and bool(os.environ.get("KAGGLE_KEY"))


def _invalid_ref(operation: str, owner: str, account: str, ref: str) -> KaggleOperationResult:
    auth = resolve_kaggle_auth(owner=owner, account=account)
    return envelope(
        "invalid_input",
        operation,
        auth,
        {"dataset_ref": ref, "error": {"error_code": "KAGGLE_DATASET_REF_INVALID", "message": "dataset_ref must look like owner/dataset-slug"}},
    )


def capabilities(*, owner: str, account: str = "default", include_quota: bool = False) -> dict[str, Any]:
    adapter = get_adapter("kaggle") if _adapter_registered() else None
    auth = resolve_kaggle_auth(owner=owner, account=account)
    snapshot: dict[str, Any] = {
        "provider": "kaggle",
        "account": account,
        "owner": owner,
        "auth": auth.to_safe_dict(),
        "credential_source": auth.source,
        "env_credentials_configured": _env_credentials_present(),
        "adapter_registered": adapter is not None and isinstance(adapter, KaggleAdapter),
        "operations": list(OPERATIONS),
        "workspace_dir": str(workspace_dir()),
        "output_max_bytes": 32_768,
    }
    if include_quota and auth.authenticated:
        _, results, failure = run_operations("quota", owner, account, [("quota", {})])
        if failure is not None:
            snapshot["quota"] = {"error": (failure.payload or {}).get("error")}
        elif results and results[0].ok:
            snapshot["quota"] = results[0].data
        elif results:
            snapshot["quota"] = {"error": results[0].error_dict()}
    return snapshot


def auth_status(*, owner: str, account: str = "default", verify: bool = False) -> dict[str, Any]:
    snapshot = capabilities(owner=owner, account=account)
    if verify and snapshot["auth"]["authenticated"]:
        _, results, failure = run_operations("whoami", owner, account, [("whoami", {})])
        if failure is not None:
            snapshot["verified"] = False
            snapshot["verify_error"] = (failure.payload or {}).get("error")
        elif results and results[0].ok:
            snapshot["verified"] = bool(results[0].data and results[0].data.get("username"))
            snapshot["username"] = (results[0].data or {}).get("username")
        elif results:
            snapshot["verified"] = False
            snapshot["verify_error"] = results[0].error_dict()
    return snapshot


def search(
    *,
    query: str,
    owner: str,
    account: str = "default",
    limit: int = 25,
) -> KaggleOperationResult:
    limit = max(1, min(limit, 50))
    fingerprint = f"{account}::search::{query.strip().lower()}::{limit}"
    cached = _RESULTS_CACHE.get(fingerprint)
    if cached is not None:
        return KaggleOperationResult(
            status=cached.status,
            operation=cached.operation,
            payload=cached.payload,
            auth_used=cached.auth_used,
            cache_hit=True,
            warnings=cached.warnings,
        )
    auth, results, failure = run_operations(
        "search", owner, account, [("dataset_list", {"query": query.strip(), "limit": limit})]
    )
    if failure is not None:
        return failure
    assert results is not None
    if not results[0].ok:
        return op_failure("search", auth, results[0])
    matches = list((results[0].data or {}).get("datasets", []))
    payload = {
        "query": query,
        "limit": limit,
        "matches": matches,
        "total_known": len(matches),
        "truncated": len(matches) >= limit,
    }
    result = envelope("ok", "search", auth, payload)
    _RESULTS_CACHE[fingerprint] = result
    return result


def get(
    *,
    dataset_ref: str,
    owner: str,
    account: str = "default",
    file_limit: int = 100,
) -> KaggleOperationResult:
    if not DATASET_REF_PATTERN.match(dataset_ref.strip()):
        return _invalid_ref("get", owner, account, dataset_ref)
    ref = dataset_ref.strip()
    auth, results, failure = run_operations(
        "get",
        owner,
        account,
        [("dataset_get", {"ref": ref}), ("dataset_files", {"ref": ref, "limit": file_limit})],
    )
    if failure is not None:
        return failure
    assert results is not None
    meta, files = results
    if not meta.ok:
        result = op_failure("get", auth, meta)
        payload = dict(result.payload or {})
        payload.update({"dataset_ref": ref, "accessible": False})
        return envelope(result.status, "get", auth, payload)
    payload = dict(meta.data or {})
    payload.update(
        {
            "dataset_ref": ref,
            "accessible": True,
            "size_bytes": payload.get("total_bytes"),
            "files": (files.data or {}).get("files", []) if files.ok else [],
            "files_truncated": bool((files.data or {}).get("has_more")) if files.ok else False,
        }
    )
    warnings = () if files.ok else ("file listing unavailable: " + str(files.error_message),)
    return envelope("ok", "get", auth, payload, warnings)


def validate(
    *,
    dataset_ref: str,
    owner: str,
    account: str = "default",
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> KaggleOperationResult:
    fetched = get(dataset_ref=dataset_ref, owner=owner, account=account, file_limit=200)
    if fetched.status in {"auth_required", "invalid_input", "error"}:
        return KaggleOperationResult(
            status=fetched.status,
            operation="validate",
            payload=fetched.payload,
            auth_used=fetched.auth_used,
        )
    payload = fetched.payload or {}
    accessible = fetched.status == "ok"
    files = payload.get("files") or []
    size = payload.get("size_bytes")
    checks = [
        {"name": "accessible", "passed": accessible, "detail": None if accessible else payload.get("error")},
        {"name": "has_files", "passed": bool(files), "detail": f"{len(files)} files listed"},
        {
            "name": "size_within_limit",
            "passed": isinstance(size, int) and size <= max_bytes,
            "detail": f"{size} bytes against limit {max_bytes}",
        },
    ]
    return KaggleOperationResult(
        status="ok",
        operation="validate",
        payload={
            "dataset_ref": dataset_ref.strip(),
            "checks": checks,
            "checks_passed": all(check["passed"] for check in checks),
        },
        auth_used=fetched.auth_used,
    )


def register(
    *,
    dataset_ref: str,
    capability: str,
    owner: str,
    account: str = "default",
) -> KaggleOperationResult:
    auth = resolve_kaggle_auth(owner=owner, account=account)
    if not DATASET_REF_PATTERN.match(dataset_ref.strip()):
        return _invalid_ref("register", owner, account, dataset_ref)
    try:
        label = require_pattern(capability.lower(), NAME_PATTERN, "KAGGLE_CAPABILITY_INVALID", "capability")
    except WorkspaceError as exc:
        return envelope("invalid_input", "register", auth, {"error": exc.to_dict()})
    path = subdir("registry") / "datasets.json"
    registered_at = datetime.now(timezone.utc).isoformat()
    try:
        with locked(path):
            registry = read_json(path, {})
            entry = registry.setdefault(dataset_ref.strip(), {"capabilities": {}})
            entry["capabilities"][label] = registered_at
            write_json(path, registry)
    except WorkspaceError as exc:
        return envelope("error", "register", auth, {"error": exc.to_dict()})
    return envelope(
        "ok",
        "register",
        auth,
        {
            "dataset_ref": dataset_ref.strip(),
            "capability": label,
            "registered_at": registered_at,
            "capabilities": sorted(entry["capabilities"]),
        },
    )


def download(
    *,
    dataset_ref: str,
    owner: str,
    account: str = "default",
    max_bytes: int = DEFAULT_MAX_BYTES,
    force: bool = False,
) -> KaggleOperationResult:
    if not DATASET_REF_PATTERN.match(dataset_ref.strip()):
        return _invalid_ref("download", owner, account, dataset_ref)
    ref = dataset_ref.strip()
    auth, results, failure = run_operations("download", owner, account, [("dataset_get", {"ref": ref})])
    if failure is not None:
        return failure
    assert results is not None
    if not results[0].ok:
        return op_failure("download", auth, results[0])
    size = (results[0].data or {}).get("total_bytes")
    if not isinstance(size, int) or size > max_bytes:
        return envelope(
            "rejected",
            "download",
            auth,
            {
                "dataset_ref": ref,
                "error": {
                    "error_code": "KAGGLE_DATASET_TOO_LARGE",
                    "message": f"dataset reports {size} bytes against max_bytes={max_bytes}; raise max_bytes explicitly or process it inside a Kaggle kernel",
                },
            },
        )
    owner_slug, _, dataset_slug = ref.partition("/")
    target = subdir("datasets", owner_slug.lower(), dataset_slug.lower())
    _, downloaded, failure = run_operations(
        "download",
        owner,
        account,
        [("dataset_download", {"ref": ref, "path": str(target), "force": force})],
        timeout=900,
    )
    if failure is not None:
        return failure
    assert downloaded is not None
    if not downloaded[0].ok:
        return op_failure("download", auth, downloaded[0])
    data = downloaded[0].data or {}
    files = data.get("files", [])
    return envelope(
        "ok",
        "download",
        auth,
        {
            "dataset_ref": ref,
            "path": data.get("path", str(target)),
            "files": files[:200],
            "file_count": len(files),
            "total_bytes": sum(int(item.get("bytes", 0)) for item in files),
        },
    )


__all__ = [
    "DEFAULT_MAX_BYTES",
    "OPERATIONS",
    "auth_status",
    "capabilities",
    "download",
    "get",
    "register",
    "reset_cache",
    "search",
    "validate",
]
