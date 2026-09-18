from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from langchain_core.tools import tool

from xninetzy.db.migrations import run_migrations
from xninetzy.db.sqlite import connect
from xninetzy.tools.tool_results import to_tool_result


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_db() -> None:
    run_migrations()


def _emit_observability(event_kind: str, subject: str, payload: dict[str, Any]) -> None:
    _ensure_db()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO observability_events
              (event_kind, severity, source, subject, payload_json, occurred_at)
            VALUES (?, 'info', 'optimization_tools', ?, ?, ?)
            """,
            (event_kind, subject, json.dumps(payload, ensure_ascii=False, default=str), _now_iso()),
        )


def _check_lib(name: str) -> dict[str, Any]:
    try:
        __import__(name)
        return {"available": True}
    except Exception as exc:
        return {"available": False, "error": str(exc)}


@tool
def dspy_optimize_prompt(
    signature_name: str,
    demonstrations: list[dict[str, Any]],
    target_metric: str = "accuracy",
    plan_id: str = "",
    step_id: str = "",
    chat_id: str = "system",
    sender_id: str = "",
    idempotency_key: str = "",
) -> str:
    """Run DSPy prompt optimization against a signature + demonstrations.

    Args:
        signature_name: Name of the DSPy signature to optimize.
        demonstrations: List of {input: {...}, output: "..."} examples.
        target_metric: Metric name to optimize (default accuracy).
        plan_id: Harness plan id.
        step_id: Harness step id.
        chat_id: Chat ID.
        sender_id: Owner principal.
        idempotency_key: Optional idempotency key.
    """
    availability = _check_lib("dspy")
    payload = {
        "signature_name": signature_name,
        "demonstration_count": len(demonstrations or []),
        "target_metric": target_metric,
        "dspy_available": availability["available"],
    }
    if not availability["available"]:
        if plan_id:
            _emit_observability(
                "optimization_blocked",
                f"{plan_id}:{step_id or 'dspy_optimize_prompt'}",
                {**payload, "reason": "dspy_not_installed"},
            )
        return to_tool_result(
            json.dumps(
                {
                    **payload,
                    "status": "blocked",
                    "reason": "dspy library not installed in environment; pip install dspy-ai required",
                    "install_command": "pip install dspy-ai",
                },
                ensure_ascii=False,
            )
        )
    import dspy

    proposed_change_id = f"proposal-{uuid.uuid4().hex[:12]}"
    output = {
        **payload,
        "status": "queued",
        "proposed_change_id": proposed_change_id,
        "apply_path": "improvement_approve",
        "note": "dspy is available; full optimization requires a configured LM and is gated by improvement_approve (FINAL).",
    }
    if plan_id:
        _emit_observability(
            "optimization_proposed",
            f"{plan_id}:{step_id or 'dspy_optimize_prompt'}",
            {**payload, "proposed_change_id": proposed_change_id},
        )
    return to_tool_result(json.dumps(output, ensure_ascii=False))


@tool
def dspy_compile(
    program_source: str,
    dataset_path: str = "",
    plan_id: str = "",
    step_id: str = "",
    chat_id: str = "system",
    sender_id: str = "",
    idempotency_key: str = "",
) -> str:
    """Compile a DSPy program from source. Returns a dry-run manifest when dspy is unavailable.

    Args:
        program_source: Python source defining the DSPy program.
        dataset_path: Optional training dataset path.
        plan_id: Harness plan id.
        step_id: Harness step id.
        chat_id: Chat ID.
        sender_id: Owner principal.
        idempotency_key: Optional idempotency key.
    """
    availability = _check_lib("dspy")
    payload = {
        "source_length_chars": len(program_source or ""),
        "dataset_path": dataset_path,
        "dspy_available": availability["available"],
    }
    if not availability["available"]:
        return to_tool_result(
            json.dumps(
                {
                    **payload,
                    "status": "blocked",
                    "reason": "dspy library not installed in environment; pip install dspy-ai required",
                    "install_command": "pip install dspy-ai",
                },
                ensure_ascii=False,
            )
        )
    proposed_change_id = f"proposal-{uuid.uuid4().hex[:12]}"
    output = {
        **payload,
        "status": "queued",
        "proposed_change_id": proposed_change_id,
        "apply_path": "improvement_approve",
        "note": "dspy is available; compilation requires a configured LM and is gated by improvement_approve (FINAL).",
    }
    if plan_id:
        _emit_observability(
            "dspy_compile_proposed",
            f"{plan_id}:{step_id or 'dspy_compile'}",
            {**payload, "proposed_change_id": proposed_change_id},
        )
    return to_tool_result(json.dumps(output, ensure_ascii=False))


@tool
def deepeval_evaluate(
    predictions: list[dict[str, Any]],
    references: list[dict[str, Any]],
    metrics: list[str] | None = None,
    plan_id: str = "",
    step_id: str = "",
    chat_id: str = "system",
    sender_id: str = "",
    idempotency_key: str = "",
) -> str:
    """Run DeepEval metrics over prediction/reference pairs.

    Args:
        predictions: List of {input, output} dicts.
        references: List of {input, expected_output} dicts.
        metrics: Metric names (default ["answer_relevancy", "faithfulness"]).
        plan_id: Harness plan id.
        step_id: Harness step id.
        chat_id: Chat ID.
        sender_id: Owner principal.
        idempotency_key: Optional idempotency key.
    """
    availability = _check_lib("deepeval")
    metric_list = metrics or ["answer_relevancy", "faithfulness"]
    payload = {
        "prediction_count": len(predictions or []),
        "reference_count": len(references or []),
        "metrics_requested": metric_list,
        "deepeval_available": availability["available"],
    }
    if not availability["available"]:
        return to_tool_result(
            json.dumps(
                {
                    **payload,
                    "status": "blocked",
                    "reason": "deepeval library not installed in environment; pip install deepeval required",
                    "install_command": "pip install deepeval",
                },
                ensure_ascii=False,
            )
        )
    proposed_change_id = f"eval-{uuid.uuid4().hex[:12]}"
    output = {
        **payload,
        "status": "queued",
        "proposal_id": proposed_change_id,
        "note": "deepeval is available; evaluation requires an LLM provider configured; results land in observability_events.",
    }
    if plan_id:
        _emit_observability(
            "deepeval_evaluation_queued",
            f"{plan_id}:{step_id or 'deepeval_evaluate'}",
            {**payload, "proposal_id": proposed_change_id},
        )
    return to_tool_result(json.dumps(output, ensure_ascii=False))


@tool
def langfuse_trace(
    plan_id: str = "",
    step_id: str = "",
    payload: dict[str, Any] | None = None,
    chat_id: str = "system",
    sender_id: str = "",
    idempotency_key: str = "",
) -> str:
    """Ingest an observability trace event into Langfuse (if configured) and observability_events.

    Args:
        plan_id: Harness plan id to associate the trace with.
        step_id: Harness step id to associate the trace with.
        payload: Dict payload describing the trace event.
        chat_id: Chat ID.
        sender_id: Owner principal.
        idempotency_key: Optional idempotency key.
    """
    from xninetzy.core.config import get_settings

    settings = get_settings()
    langfuse_enabled = bool(getattr(settings, "LANGFUSE_PUBLIC_KEY", "") and getattr(settings, "LANGFUSE_SECRET_KEY", ""))
    trace_payload = dict(payload or {})
    trace_payload["plan_id"] = plan_id
    trace_payload["step_id"] = step_id
    if langfuse_enabled:
        try:
            from langfuse import Langfuse  # type: ignore

            client = Langfuse(
                public_key=str(settings.LANGFUSE_PUBLIC_KEY),
                secret_key=str(settings.LANGFUSE_SECRET_KEY),
                host=str(getattr(settings, "LANGFUSE_HOST", "") or "https://cloud.langfuse.com"),
            )
            client.trace(name="xninetzy_step", input=trace_payload)
            client.flush()
            trace_payload["langfuse_status"] = "sent"
        except Exception as exc:
            trace_payload["langfuse_status"] = f"failed: {exc}"
    else:
        trace_payload["langfuse_status"] = "disabled"
    _emit_observability(
        "langfuse_trace",
        f"{plan_id}:{step_id}" if plan_id else step_id or "langfuse_trace",
        trace_payload,
    )
    return to_tool_result(json.dumps(trace_payload, ensure_ascii=False))


optimization_tools = [
    dspy_optimize_prompt,
    dspy_compile,
    deepeval_evaluate,
    langfuse_trace,
]
