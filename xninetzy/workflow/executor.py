"""Runs a WorkflowPlan action-by-action with WA progress notifications.

Behaviour:
  * actions run in order (linear dependency); a dependency that did not succeed
    causes the dependent action to be skipped.
  * non-critical failures are logged + notified, then the workflow continues;
    a critical failure stops the workflow and synthesises a partial result.
  * the final FINAL_SYNTHESIS step assembles every step summary into one reply.

Runs inline within the current request (no background queue) — see
``WorkflowRunnerMode``. We never claim to "do it later".
"""

from __future__ import annotations

import time

from app.xninetzy.core.config import get_settings
from app.xninetzy.core.logging import logging
from app.xninetzy.workflow.actions import execute_action
from app.xninetzy.workflow.models import (
    WorkflowAction,
    WorkflowActionResult,
    WorkflowActionStatus,
    WorkflowActionType,
    WorkflowExecutionResult,
    WorkflowPlan,
    WorkflowState,
)
from app.xninetzy.workflow.notifier import WorkflowNotifier

logger = logging.getLogger(__name__)


class WorkflowExecutor:
    def __init__(self, *, notifier: WorkflowNotifier | None = None, handlers=None, store=None):
        self.notifier = notifier
        self.handlers = handlers
        self.store = store

    async def execute(
        self, plan: WorkflowPlan, state: WorkflowState | None = None
    ) -> WorkflowExecutionResult:
        st = state or WorkflowState(
            plan_id=plan.id, chat_id=plan.chat_id,
            original_user_message=plan.original_user_message,
        )
        results: list[WorkflowActionResult] = []
        succeeded_ids: set[str] = set()
        skipped_ids: set[str] = set()
        stopped = False

        if self.store:
            self.store.save_plan(plan)

        for action in plan.actions:
            # Only a *skipped* dependency cascades. A non-critical failure does
            # NOT block downstream (spec: "download gagal → tetap lanjut planning").
            unmet = [d for d in action.depends_on if d in skipped_ids]
            if unmet:
                skipped_ids.add(action.id)
                action.status = WorkflowActionStatus.SKIPPED
                action.result_summary = "Dilewati: langkah sebelumnya tidak selesai."
                results.append(WorkflowActionResult(
                    action_id=action.id, status=WorkflowActionStatus.SKIPPED,
                    summary=action.result_summary,
                ))
                logger.info("workflow_action_skipped workflow_id=%s action_id=%s type=%s",
                            plan.id, action.id, action.type.value)
                self._persist_action(action, plan.id)
                continue

            action.status = WorkflowActionStatus.RUNNING
            started = time.monotonic()
            logger.info("workflow_action_started workflow_id=%s action_id=%s type=%s",
                        plan.id, action.id, action.type.value)
            if self.notifier:
                await self.notifier.notify_action_started(plan, action)

            result = await execute_action(action, st, self.handlers)
            duration_ms = int((time.monotonic() - started) * 1000)
            action.status = result.status
            action.result_summary = result.summary
            action.error = result.error
            results.append(result)

            if result.status == WorkflowActionStatus.SUCCESS:
                succeeded_ids.add(action.id)
                if result.summary:
                    st.summaries.append(result.summary)
                logger.info(
                    "workflow_action_success workflow_id=%s action_id=%s type=%s duration_ms=%d",
                    plan.id, action.id, action.type.value, duration_ms,
                )
                if self.notifier:
                    await self.notifier.notify_action_done(plan, action)
            else:
                logger.info(
                    "workflow_action_failed workflow_id=%s action_id=%s type=%s "
                    "duration_ms=%d critical=%s error_type=%s",
                    plan.id, action.id, action.type.value, duration_ms,
                    action.critical, type(action.error).__name__,
                )
                if self.notifier:
                    await self.notifier.notify_action_failed(plan, action)
                if action.critical:
                    stopped = True
                    self._persist_action(action, plan.id)
                    break

            self._persist_action(action, plan.id)

        final_response = self._build_final_response(plan, st, results, stopped)
        overall = (
            WorkflowActionStatus.FAILED if stopped
            else WorkflowActionStatus.SUCCESS
        )
        exec_result = WorkflowExecutionResult(
            plan_id=plan.id, status=overall, final_response=final_response,
            action_results=results,
        )
        if self.store:
            self.store.save_result(plan, exec_result)
        if self.notifier:
            await self.notifier.notify_final(plan, self._one_line(plan, results))
        logger.info("workflow_final_synthesis_created workflow_id=%s status=%s",
                    plan.id, overall.value)
        return exec_result

    # ── synthesis ────────────────────────────────────────────────────────────

    def _build_final_response(self, plan, state, results, stopped) -> str:
        # Prefer the FINAL_SYNTHESIS step's output if it ran.
        final = next(
            (r for r, a in zip(results, plan.actions)
             if a.type == WorkflowActionType.FINAL_SYNTHESIS
             and r.status == WorkflowActionStatus.SUCCESS),
            None,
        )
        succeeded = [r for r in results if r.status == WorkflowActionStatus.SUCCESS
                     and r.summary and not _is_final(plan, r)]
        failed = [r for r in results if r.status == WorkflowActionStatus.FAILED]
        skipped = [r for r in results if r.status == WorkflowActionStatus.SKIPPED]

        if final and not failed and not skipped:
            return final.summary or "Workflow selesai."

        header = "✅ *Workflow selesai sebagian*" if (failed or skipped or stopped) else "✅ *Workflow selesai*"
        lines = [header, ""]
        if succeeded:
            lines.append("*Berhasil:*")
            lines += [f"- {r.summary}" for r in succeeded]
        if failed:
            lines += ["", "*Belum berhasil:*"] + [f"- {r.error}" for r in failed]
        if skipped:
            lines += ["", "*Dilewati:*"] + [f"- {r.summary}" for r in skipped]
        if state.obsidian_paths:
            lines += ["", "*Catatan tersimpan:*"] + [f"- `{p}`" for p in state.obsidian_paths]
        return "\n".join(lines).strip()

    def _one_line(self, plan, results) -> str:
        ok = sum(1 for r in results if r.status == WorkflowActionStatus.SUCCESS)
        return f"{ok}/{len(results)} langkah berhasil."

    def _persist_action(self, action: WorkflowAction, workflow_id: str) -> None:
        if self.store:
            try:
                self.store.save_action(action, workflow_id)
            except Exception:  # pragma: no cover
                pass


def _is_final(plan: WorkflowPlan, result: WorkflowActionResult) -> bool:
    for a in plan.actions:
        if a.id == result.action_id:
            return a.type == WorkflowActionType.FINAL_SYNTHESIS
    return False


async def run_workflow(
    chat_id: str, user_message: str, *, context: dict | None = None, from_whatsapp: bool = True
) -> str:
    """High-level entry: build a plan, execute it, return the final reply text."""
    from app.xninetzy.workflow.plan import build_workflow_plan

    settings = get_settings()
    plan = await build_workflow_plan(chat_id, user_message, context)
    notifier = (
        WorkflowNotifier(chat_id)
        if (from_whatsapp and settings.WORKFLOW_NOTIFY_ENABLED)
        else None
    )
    store = None
    try:
        from app.xninetzy.workflow.store import WorkflowStore
        store = WorkflowStore()
    except Exception:  # pragma: no cover
        store = None

    state = WorkflowState(
        plan_id=plan.id, chat_id=chat_id, original_user_message=user_message,
        from_whatsapp=from_whatsapp,
    )
    executor = WorkflowExecutor(notifier=notifier, store=store)
    result = await executor.execute(plan, state)
    return result.final_response
