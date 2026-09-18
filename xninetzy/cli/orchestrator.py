from __future__ import annotations

import argparse
import asyncio
import json
import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import yaml

from xninetzy.core.logging import logging
from xninetzy.os.research.sources.base import stable_idempotency_key
from xninetzy.tools.registry import get_all_tools

logger = logging.getLogger(__name__)


_VALID_TIERS = {0, 1, 2, 3}


@dataclass
class StepResult:
    step_id: str
    tool: str
    status: str
    output: Any = None
    error: str | None = None
    idempotency_key: str = ""
    started_at: str = ""
    finished_at: str = ""


@dataclass
class PlanResult:
    plan_id: str
    title: str
    status: str
    steps: list[StepResult] = field(default_factory=list)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _validate_plan(plan: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not isinstance(plan, dict):
        return ["plan must be a mapping"]
    steps = plan.get("steps")
    if not isinstance(steps, list) or not steps:
        return ["plan.steps must be a non-empty list"]
    step_ids: set[str] = set()
    for idx, step in enumerate(steps):
        if not isinstance(step, dict):
            errors.append(f"step[{idx}] must be a mapping")
            continue
        sid = str(step.get("id") or "").strip()
        if not sid:
            errors.append(f"step[{idx}] missing id")
        elif sid in step_ids:
            errors.append(f"step[{idx}] duplicate id: {sid}")
        step_ids.add(sid)
        tool = step.get("tool")
        if not tool or not isinstance(tool, str):
            errors.append(f"step[{idx}] missing tool name")
        tier = step.get("tier", 0)
        if tier not in _VALID_TIERS:
            errors.append(f"step[{idx}] invalid tier: {tier}")
    return errors


def _resolve_idempotency(step: dict[str, Any], plan_id: str) -> str:
    raw = str(step.get("idempotency_key") or "").strip()
    if raw and raw != "auto":
        return raw
    args = step.get("args") or {}
    seed = f"{plan_id}|{step.get('id')}|{step.get('tool')}|{json.dumps(args, sort_keys=True)}"
    return stable_idempotency_key(seed)


def _build_tool_map() -> dict[str, Any]:
    return {tool.name: tool for tool in get_all_tools()}


async def _run_step(step: dict[str, Any], plan_id: str, tool_map: dict[str, Any]) -> StepResult:
    sid = str(step.get("id") or f"step-{uuid.uuid4().hex[:8]}")
    tool_name = str(step.get("tool") or "")
    tier = int(step.get("tier", 0))
    args = dict(step.get("args") or {})
    idempotency_key = _resolve_idempotency(step, plan_id)
    started_at = _now_iso()
    if tool_name not in tool_map:
        return StepResult(
            step_id=sid,
            tool=tool_name,
            status="unknown_tool",
            error=f"tool '{tool_name}' is not registered",
            idempotency_key=idempotency_key,
            started_at=started_at,
            finished_at=_now_iso(),
        )
    if tier >= 2:
        return StepResult(
            step_id=sid,
            tool=tool_name,
            status="halted",
            error=f"tier {tier} requires explicit owner approval; run with --approve <approval_id> to execute",
            idempotency_key=idempotency_key,
            started_at=started_at,
            finished_at=_now_iso(),
        )
    args.setdefault("plan_id", plan_id)
    args.setdefault("step_id", sid)
    if idempotency_key and "idempotency_key" not in args:
        args["idempotency_key"] = idempotency_key
    tool = tool_map[tool_name]
    try:
        output = await tool.ainvoke(args)
        return StepResult(
            step_id=sid,
            tool=tool_name,
            status="ok",
            output=output,
            idempotency_key=idempotency_key,
            started_at=started_at,
            finished_at=_now_iso(),
        )
    except Exception as exc:
        return StepResult(
            step_id=sid,
            tool=tool_name,
            status="error",
            error=str(exc),
            idempotency_key=idempotency_key,
            started_at=started_at,
            finished_at=_now_iso(),
        )


async def execute_plan(plan: dict[str, Any], approval_id: str | None = None) -> PlanResult:
    plan_id = str(plan.get("id") or f"plan-{uuid.uuid4().hex[:12]}")
    title = str(plan.get("title") or "Untitled plan")
    tool_map = _build_tool_map()
    results: list[StepResult] = []
    for step in plan.get("steps") or []:
        if not isinstance(step, dict):
            continue
        if approval_id:
            step.setdefault("approval_id", approval_id)
        result = await _run_step(step, plan_id, tool_map)
        results.append(result)
        if result.status in {"error", "halted"}:
            return PlanResult(plan_id=plan_id, title=title, status="partial", steps=results)
    return PlanResult(plan_id=plan_id, title=title, status="ok", steps=results)


def _format_result(result: PlanResult) -> str:
    payload = {
        "plan_id": result.plan_id,
        "title": result.title,
        "status": result.status,
        "steps": [
            {
                "step_id": r.step_id,
                "tool": r.tool,
                "status": r.status,
                "idempotency_key": r.idempotency_key,
                "started_at": r.started_at,
                "finished_at": r.finished_at,
                "error": r.error,
                "output": r.output if r.status == "ok" else None,
            }
            for r in result.steps
        ],
    }
    return json.dumps(payload, ensure_ascii=False, default=str)


def _run_validate(path: str) -> int:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            plan = yaml.safe_load(handle)
    except Exception as exc:
        print(f"failed to load plan: {exc}", file=sys.stderr)
        return 2
    errors = _validate_plan(plan)
    if errors:
        for err in errors:
            print(f"error: {err}", file=sys.stderr)
        return 1
    print("plan valid")
    return 0


def _run_execute(path: str, approval_id: str | None) -> int:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            plan = yaml.safe_load(handle)
    except Exception as exc:
        print(f"failed to load plan: {exc}", file=sys.stderr)
        return 2
    errors = _validate_plan(plan)
    if errors:
        for err in errors:
            print(f"error: {err}", file=sys.stderr)
        return 1
    try:
        result = asyncio.run(execute_plan(plan, approval_id=approval_id))
    except Exception as exc:
        print(f"execution failed: {exc}", file=sys.stderr)
        return 3
    print(_format_result(result))
    return 0 if result.status == "ok" else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="xninetzy-cli")
    sub = parser.add_subparsers(dest="command", required=True)
    validate_p = sub.add_parser("validate")
    validate_p.add_argument("plan")
    run_p = sub.add_parser("run")
    run_p.add_argument("plan")
    run_p.add_argument("--approve", dest="approval_id", default=None)
    args = parser.parse_args(argv)
    if args.command == "validate":
        return _run_validate(args.plan)
    if args.command == "run":
        return _run_execute(args.plan, args.approval_id)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
