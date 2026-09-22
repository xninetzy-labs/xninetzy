from __future__ import annotations

from langchain_core.tools import tool

from xninetzy.interfaces.tasks_extension import (
    TaskRecord,
    TaskStatus,
    cancel as cancel_task,
    create_task,
    get_task,
    list_tasks,
    result_of,
    transition,
)
from xninetzy.tools.tool_results import to_tool_result


def _uid(sender_id: str | None, chat_id: str | None) -> str:
    return (sender_id or chat_id or "default").strip() or "default"


@tool
def tasks_create(
    tool_name: str,
    arguments_json: str = "{}",
    idempotency_key: str = "",
    sender_id: str = "",
    chat_id: str = "",
    task_id: str = "",
) -> str:
    """Create a durable MCP task handle (SEP-2663). The task records the
    intended tool name + arguments and a ``QUEUED`` status. The result
    field is empty until :func:`tasks_complete` is called with the
    final result.

    Arguments:
        tool_name: name of the tool that will populate the result.
        arguments_json: JSON-encoded argument bag forwarded to the tool.
        idempotency_key: optional key; re-using it returns the existing task.
        sender_id: owner principal (injected by the MCP adapter).
        chat_id: chat principal (injected by the MCP adapter).
        task_id: optional explicit task id (auto-generated when omitted).
    """
    import json as _json

    try:
        arguments = _json.loads(arguments_json) if arguments_json else {}
        if not isinstance(arguments, dict):
            arguments = {"value": arguments}
    except Exception as exc:
        return to_tool_result({"error": f"invalid arguments_json: {exc}"})
    record = create_task(
        tool_name=tool_name,
        arguments=arguments,
        owner=_uid(sender_id, chat_id),
        chat_id=chat_id or _uid(sender_id, chat_id),
        idempotency_key=idempotency_key or None,
        task_id=task_id or None,
    )
    return to_tool_result(record.to_dict())


@tool
def tasks_get(task_id: str) -> str:
    """Return the current record for a task by id."""
    record = get_task(task_id)
    if record is None:
        return to_tool_result({"error": f"unknown task: {task_id}"})
    return to_tool_result(record.to_dict())


@tool
def tasks_list(
    statuses: list[str] | None = None,
    limit: int = 20,
    sender_id: str = "",
    chat_id: str = "",
) -> str:
    """List recent tasks owned by the calling principal."""
    parsed_statuses: list[TaskStatus] = []
    for s in statuses or []:
        try:
            parsed_statuses.append(TaskStatus(s))
        except ValueError:
            return to_tool_result({"error": f"invalid status: {s}"})
    records = list_tasks(
        owner=_uid(sender_id, chat_id),
        chat_id=chat_id or None,
        statuses=parsed_statuses or None,
        limit=int(limit),
    )
    return to_tool_result({
        "count": len(records),
        "tasks": [r.to_dict() for r in records],
    })


@tool
def tasks_cancel(task_id: str) -> str:
    """Cancel a running or queued task. No-op if the task already terminated."""
    record = cancel_task(task_id)
    if record is None:
        return to_tool_result({"error": f"unknown task: {task_id}"})
    return to_tool_result(record.to_dict())


@tool
def tasks_complete(
    task_id: str,
    result_json: str = "",
    error: str = "",
    success: bool = True,
) -> str:
    """Mark a task as completed (success=True) or failed (success=False).
    Result must be a JSON-serialisable string when success=True."""
    import json as _json

    if success:
        try:
            result = _json.loads(result_json) if result_json else None
        except Exception as exc:
            return to_tool_result({"error": f"invalid result_json: {exc}"})
        record = transition(task_id, to=TaskStatus.COMPLETED, result=result)
    else:
        record = transition(task_id, to=TaskStatus.FAILED, error=error or "task failed")
    if record is None:
        return to_tool_result({"error": f"unknown task: {task_id}"})
    return to_tool_result(record.to_dict())


@tool
def tasks_result(task_id: str) -> str:
    """Return the terminal result of a task. For tasks still running this
    returns the current status and ``updated_at`` instead of a result body."""
    return to_tool_result(result_of(task_id))


__all__ = [
    "tasks_create",
    "tasks_get",
    "tasks_list",
    "tasks_cancel",
    "tasks_complete",
    "tasks_result",
    "TaskRecord",
]
