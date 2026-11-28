from __future__ import annotations

from typing import Any

from langchain_core.tools import BaseTool

from xninetzy.integrations.kaggle import services as kaggle_services
from xninetzy.integrations.kaggle.auth_adapter import kaggle_auth_required_error
from xninetzy.integrations.kaggle.services.datasets import DEFAULT_MAX_BYTES
from xninetzy.tools.tool_results import to_tool_result


def _owner(sender_id: str | None, chat_id: str | None) -> str:
    return sender_id or chat_id or "local-owner"


def _respond(result: Any, sender_id: str | None, chat_id: str | None) -> str:
    payload: dict[str, Any] = {
        "status": result.status,
        "operation": result.operation,
        "auth_used": result.auth_used,
    }
    if result.cache_hit:
        payload["cache_hit"] = True
    if result.warnings:
        payload["warnings"] = list(result.warnings)
    if result.payload is not None:
        payload["payload"] = result.payload
    if result.status == "auth_required":
        payload["error"] = kaggle_auth_required_error()
    return to_tool_result(payload, sender_id=sender_id, chat_id=chat_id)


def kaggle_capabilities(
    sender_id: str | None = None,
    chat_id: str | None = None,
    account: str = "default",
    include_quota: bool = False,
) -> str:
    owner = _owner(sender_id, chat_id)
    snapshot = kaggle_services.capabilities(owner=owner, account=account, include_quota=include_quota)
    return to_tool_result(snapshot, sender_id=sender_id, chat_id=chat_id)


def kaggle_auth_status(
    sender_id: str | None = None,
    chat_id: str | None = None,
    account: str = "default",
    verify: bool = False,
) -> str:
    owner = _owner(sender_id, chat_id)
    snapshot = kaggle_services.auth_status(owner=owner, account=account, verify=verify)
    auth = snapshot.get("auth", {})
    if not auth.get("authenticated") and not snapshot.get("env_credentials_configured"):
        payload = dict(snapshot)
        payload["next_step"] = "kaggle_auth_required"
        payload["error"] = kaggle_auth_required_error()
        return to_tool_result(payload, sender_id=sender_id, chat_id=chat_id)
    return to_tool_result(snapshot, sender_id=sender_id, chat_id=chat_id)


def kaggle_dataset_search(
    query: str,
    limit: int = 25,
    sender_id: str | None = None,
    chat_id: str | None = None,
    account: str = "default",
) -> str:
    result = kaggle_services.search(
        query=query,
        owner=_owner(sender_id, chat_id),
        account=account,
        limit=limit,
    )
    return _respond(result, sender_id, chat_id)


def kaggle_dataset_get(
    dataset_ref: str,
    sender_id: str | None = None,
    chat_id: str | None = None,
    account: str = "default",
) -> str:
    result = kaggle_services.get(
        dataset_ref=dataset_ref,
        owner=_owner(sender_id, chat_id),
        account=account,
    )
    return _respond(result, sender_id, chat_id)


def kaggle_dataset_register(
    dataset_ref: str,
    capability: str,
    sender_id: str | None = None,
    chat_id: str | None = None,
    account: str = "default",
) -> str:
    result = kaggle_services.register(
        dataset_ref=dataset_ref,
        capability=capability,
        owner=_owner(sender_id, chat_id),
        account=account,
    )
    return _respond(result, sender_id, chat_id)


def kaggle_dataset_validate(
    dataset_ref: str,
    max_bytes: int = DEFAULT_MAX_BYTES,
    sender_id: str | None = None,
    chat_id: str | None = None,
    account: str = "default",
) -> str:
    result = kaggle_services.validate(
        dataset_ref=dataset_ref,
        owner=_owner(sender_id, chat_id),
        account=account,
        max_bytes=max_bytes,
    )
    return _respond(result, sender_id, chat_id)


def kaggle_dataset_download(
    dataset_ref: str,
    max_bytes: int = DEFAULT_MAX_BYTES,
    force: bool = False,
    idempotency_key: str = "",
    sender_id: str | None = None,
    chat_id: str | None = None,
    account: str = "default",
) -> str:
    result = kaggle_services.download(
        dataset_ref=dataset_ref,
        owner=_owner(sender_id, chat_id),
        account=account,
        max_bytes=max_bytes,
        force=force,
    )
    return _respond(result, sender_id, chat_id)


def kaggle_kernel_push(
    slug: str,
    idempotency_key: str = "",
    source: str = "",
    source_path: str = "",
    job: dict[str, Any] | None = None,
    gpu: bool = False,
    accelerator: str = "",
    internet: bool = True,
    dataset_sources: list[str] | None = None,
    kernel_sources: list[str] | None = None,
    time_budget_seconds: int = 3600,
    sender_id: str | None = None,
    chat_id: str | None = None,
    account: str = "default",
) -> str:
    result = kaggle_services.kernel_push(
        owner=_owner(sender_id, chat_id),
        account=account,
        slug=slug,
        idempotency_key=idempotency_key,
        source=source or None,
        source_path=source_path or None,
        job=job,
        gpu=gpu,
        accelerator=accelerator,
        internet=internet,
        dataset_sources=dataset_sources or [],
        kernel_sources=kernel_sources or [],
        time_budget_seconds=time_budget_seconds,
    )
    return _respond(result, sender_id, chat_id)


def kaggle_kernel_status(
    slug: str,
    sender_id: str | None = None,
    chat_id: str | None = None,
    account: str = "default",
) -> str:
    result = kaggle_services.kernel_status(
        owner=_owner(sender_id, chat_id),
        account=account,
        slug=slug,
    )
    return _respond(result, sender_id, chat_id)


def kaggle_kernel_output(
    slug: str,
    read: list[str] | None = None,
    max_read_bytes: int = 16_384,
    log_tail_chars: int = 0,
    live_log_seconds: int = 0,
    page_token: str = "",
    sender_id: str | None = None,
    chat_id: str | None = None,
    account: str = "default",
) -> str:
    result = kaggle_services.kernel_output(
        owner=_owner(sender_id, chat_id),
        account=account,
        slug=slug,
        read=read or [],
        max_read_bytes=max_read_bytes,
        log_tail_chars=log_tail_chars,
        live_log_seconds=live_log_seconds,
        page_token=page_token or None,
    )
    return _respond(result, sender_id, chat_id)


def kaggle_pipeline_plan(
    name: str,
    jobs: list[dict[str, Any]],
    limits: dict[str, int] | None = None,
    replace: bool = False,
    sender_id: str | None = None,
    chat_id: str | None = None,
    account: str = "default",
) -> str:
    result = kaggle_services.pipeline_plan(
        owner=_owner(sender_id, chat_id),
        account=account,
        name=name,
        jobs=jobs,
        limits=limits,
        replace=replace,
    )
    return _respond(result, sender_id, chat_id)


def kaggle_pipeline_status(
    name: str = "",
    sender_id: str | None = None,
    chat_id: str | None = None,
    account: str = "default",
) -> str:
    result = kaggle_services.pipeline_status(
        owner=_owner(sender_id, chat_id),
        account=account,
        name=name,
    )
    return _respond(result, sender_id, chat_id)


def kaggle_pipeline_tick(
    name: str,
    idempotency_key: str = "",
    sender_id: str | None = None,
    chat_id: str | None = None,
    account: str = "default",
    reconcile_jobs: list[str] | None = None,
    restart_cancelled: list[str] | None = None,
    resume_partial: list[str] | None = None,
    accept_unavailable: list[str] | None = None,
    accept_unextractable: list[str] | None = None,
    requeue_back: list[str] | None = None,
) -> str:
    result = kaggle_services.pipeline_tick(
        owner=_owner(sender_id, chat_id),
        account=account,
        name=name,
        idempotency_key=idempotency_key,
        reconcile_jobs=reconcile_jobs,
        restart_cancelled=restart_cancelled,
        resume_partial=resume_partial,
        accept_unavailable=accept_unavailable,
        accept_unextractable=accept_unextractable,
        requeue_back=requeue_back,
    )
    return _respond(result, sender_id, chat_id)


kaggle_capabilities_tool: BaseTool = kaggle_capabilities  # type: ignore[assignment]
kaggle_auth_status_tool: BaseTool = kaggle_auth_status  # type: ignore[assignment]
kaggle_dataset_search_tool: BaseTool = kaggle_dataset_search  # type: ignore[assignment]
kaggle_dataset_get_tool: BaseTool = kaggle_dataset_get  # type: ignore[assignment]
kaggle_dataset_register_tool: BaseTool = kaggle_dataset_register  # type: ignore[assignment]
kaggle_dataset_validate_tool: BaseTool = kaggle_dataset_validate  # type: ignore[assignment]


__all__ = [
    "kaggle_auth_status",
    "kaggle_capabilities",
    "kaggle_dataset_download",
    "kaggle_dataset_get",
    "kaggle_dataset_register",
    "kaggle_dataset_search",
    "kaggle_dataset_validate",
    "kaggle_kernel_output",
    "kaggle_kernel_push",
    "kaggle_kernel_status",
    "kaggle_pipeline_plan",
    "kaggle_pipeline_status",
    "kaggle_pipeline_tick",
]
