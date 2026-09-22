from __future__ import annotations

from typing import Any

from langchain_core.tools import BaseTool

from xninetzy.integrations.kaggle import services as kaggle_services
from xninetzy.integrations.kaggle.auth_adapter import kaggle_auth_required_error
from xninetzy.tools.tool_results import to_tool_result


def _owner(sender_id: str | None, chat_id: str | None) -> str:
    return sender_id or chat_id or "local-owner"


def kaggle_capabilities(
    sender_id: str | None = None,
    chat_id: str | None = None,
    account: str = "default",
) -> dict[str, Any]:
    owner = _owner(sender_id, chat_id)
    snapshot = kaggle_services.capabilities(owner=owner, account=account)
    return to_tool_result(snapshot, sender_id=sender_id, chat_id=chat_id)


def kaggle_auth_status(
    sender_id: str | None = None,
    chat_id: str | None = None,
    account: str = "default",
) -> dict[str, Any]:
    owner = _owner(sender_id, chat_id)
    snapshot = kaggle_services.capabilities(owner=owner, account=account)
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
) -> dict[str, Any]:
    owner = _owner(sender_id, chat_id)
    result = kaggle_services.search(
        query=query,
        owner=owner,
        account=account,
        limit=limit,
    )
    payload: dict[str, Any] = {
        "status": result.status,
        "operation": result.operation,
        "auth_used": result.auth_used,
        "cache_hit": result.cache_hit,
        "warnings": list(result.warnings),
    }
    if result.payload is not None:
        payload["payload"] = result.payload
    if result.status == "auth_required":
        payload["error"] = kaggle_auth_required_error()
    return to_tool_result(payload, sender_id=sender_id, chat_id=chat_id)


def kaggle_dataset_get(
    dataset_ref: str,
    sender_id: str | None = None,
    chat_id: str | None = None,
    account: str = "default",
) -> dict[str, Any]:
    owner = _owner(sender_id, chat_id)
    result = kaggle_services.get(
        dataset_ref=dataset_ref,
        owner=owner,
        account=account,
    )
    payload: dict[str, Any] = {
        "status": result.status,
        "operation": result.operation,
        "auth_used": result.auth_used,
    }
    if result.payload is not None:
        payload["payload"] = result.payload
    if result.status == "auth_required":
        payload["error"] = kaggle_auth_required_error()
    return to_tool_result(payload, sender_id=sender_id, chat_id=chat_id)


def kaggle_dataset_register(
    dataset_ref: str,
    capability: str,
    sender_id: str | None = None,
    chat_id: str | None = None,
    account: str = "default",
) -> dict[str, Any]:
    owner = _owner(sender_id, chat_id)
    result = kaggle_services.register(
        dataset_ref=dataset_ref,
        capability=capability,
        owner=owner,
        account=account,
    )
    payload: dict[str, Any] = {
        "status": result.status,
        "operation": result.operation,
        "auth_used": result.auth_used,
    }
    if result.payload is not None:
        payload["payload"] = result.payload
    return to_tool_result(payload, sender_id=sender_id, chat_id=chat_id)


def kaggle_dataset_validate(
    dataset_ref: str,
    sender_id: str | None = None,
    chat_id: str | None = None,
    account: str = "default",
) -> dict[str, Any]:
    owner = _owner(sender_id, chat_id)
    result = kaggle_services.validate(
        dataset_ref=dataset_ref,
        owner=owner,
        account=account,
    )
    payload: dict[str, Any] = {
        "status": result.status,
        "operation": result.operation,
        "auth_used": result.auth_used,
    }
    if result.payload is not None:
        payload["payload"] = result.payload
    return to_tool_result(payload, sender_id=sender_id, chat_id=chat_id)


kaggle_capabilities_tool: BaseTool = kaggle_capabilities  # type: ignore[assignment]
kaggle_auth_status_tool: BaseTool = kaggle_auth_status  # type: ignore[assignment]
kaggle_dataset_search_tool: BaseTool = kaggle_dataset_search  # type: ignore[assignment]
kaggle_dataset_get_tool: BaseTool = kaggle_dataset_get  # type: ignore[assignment]
kaggle_dataset_register_tool: BaseTool = kaggle_dataset_register  # type: ignore[assignment]
kaggle_dataset_validate_tool: BaseTool = kaggle_dataset_validate  # type: ignore[assignment]


__all__ = [
    "kaggle_auth_status",
    "kaggle_capabilities",
    "kaggle_dataset_get",
    "kaggle_dataset_register",
    "kaggle_dataset_search",
    "kaggle_dataset_validate",
]
