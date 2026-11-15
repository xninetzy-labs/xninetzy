"""Runs a WorkflowPlan action-by-action with owner progress notifications.

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
from contextlib import nullcontext

from xninetzy.core.config import get_settings
from xninetzy.core.logging import logging
from xninetzy.core.security import sanitize_tool_output
from xninetzy.workflow.actions import execute_action
from xninetzy.workflow.models import (
    WorkflowAction,
    WorkflowActionResult,
    WorkflowActionStatus,
    WorkflowActionType,
    WorkflowExecutionResult,
    WorkflowPlan,
    WorkflowState,
    WorkflowCheckpoint,
)
from xninetzy.workflow.notifier import WorkflowNotifier
from xninetzy.workflow.store import WorkflowRecoveryError, plan_fingerprint

logger = logging.getLogger(__name__)

_SAFE_RETRY = {
    WorkflowActionType.REMINDER_LIST, WorkflowActionType.FINAL_SYNTHESIS,
    WorkflowActionType.WEB_SEARCH, WorkflowActionType.YOUTUBE_SEARCH, WorkflowActionType.PAPER_SEARCH,
    WorkflowActionType.HEBAT_COURSE_DETAIL, WorkflowActionType.HEBAT_ASSIGNMENT_DETAIL,
}


class WorkflowExecutor:
    def __init__(self, *, notifier: WorkflowNotifier | None = None, handlers=None, store=None):
        self.notifier = notifier
        self.handlers = handlers
        self.store = store

    async def execute(
        self, plan: WorkflowPlan, state: WorkflowState | None = None, *, resume: bool = False,
    ) -> WorkflowExecutionResult:
        try:
            ids = [a.id for a in plan.actions]
            if len(ids) != len(set(ids)) or len(ids) > get_settings().WORKFLOW_MAX_ACTIONS:
                raise WorkflowRecoveryError("workflow_plan_invalid")
            seen = set()
            for action in plan.actions:
                if any(dependency not in seen for dependency in action.depends_on):
                    raise WorkflowRecoveryError("workflow_dependencies_invalid")
                seen.add(action.id)
            st = state or WorkflowState(plan_id=plan.id, chat_id=plan.chat_id, original_user_message=plan.original_user_message)
            if st.plan_id != plan.id or st.chat_id != plan.chat_id or st.original_user_message != plan.original_user_message:
                raise WorkflowRecoveryError("workflow_owner_mismatch")
            if self.store:
                from xninetzy.os.policy.action_policy import evaluate_action
                decision = evaluate_action("workflow_resume")
                if not decision.allowed or decision.requires_approval:
                    raise WorkflowRecoveryError("workflow_policy_held")
            with self.store.execution_lock(plan.id) if self.store else nullcontext():
                previous = None
                if self.store:
                    row = self.store.get(plan.id)
                    if row:
                        if row["chat_id"] != plan.chat_id:
                            raise WorkflowRecoveryError("workflow_owner_mismatch")
                        if row["status"] == "cancelled":
                            raise WorkflowRecoveryError("workflow_cancelled")
                        previous = self.store.restore_checkpoint(plan)
                        if row["status"] == "success":
                            if any(a.status != WorkflowActionStatus.SUCCESS for a in plan.actions):
                                raise WorkflowRecoveryError("workflow_completion_unverified")
                            return previous.model_copy(update={"final_response": "Hasil tersimpan (tanpa eksekusi ulang):\n" + previous.final_response})
                        if not resume:
                            raise WorkflowRecoveryError("workflow_already_exists_use_resume")
                        for action in plan.actions:
                            if action.status not in {WorkflowActionStatus.PENDING, WorkflowActionStatus.SUCCESS}:
                                if action.type not in _SAFE_RETRY:
                                    raise WorkflowRecoveryError("workflow_uncertain_outcome_reconcile")
                                if any(a.status == WorkflowActionStatus.SUCCESS and action.id in a.depends_on for a in plan.actions):
                                    raise WorkflowRecoveryError("workflow_completed_dependency_requires_review")
                        st = previous.checkpoint.state
                    elif resume:
                        raise WorkflowRecoveryError("workflow_not_found")
                    else:
                        self.store.save_plan(plan, st)
                return await self._execute(plan, st, previous=previous)
        except WorkflowRecoveryError as exc:
            return WorkflowExecutionResult(plan_id=plan.id, status=WorkflowActionStatus.FAILED, final_response=f"Pekerjaan ditahan: {exc}. Periksa checkpoint sebelum mengulang aksi.")
        except Exception as exc:
            logger.warning("workflow_checkpoint_error type=%s", type(exc).__name__)
            return WorkflowExecutionResult(plan_id=plan.id, status=WorkflowActionStatus.FAILED, final_response="workflow_checkpoint_unverified: periksa state dan penyimpanan sebelum melanjutkan.")

    async def _execute(
        self, plan: WorkflowPlan, state: WorkflowState | None = None, *, previous=None,
    ) -> WorkflowExecutionResult:
        st = state or WorkflowState(
            plan_id=plan.id, chat_id=plan.chat_id,
            original_user_message=plan.original_user_message,
        )
        prior = {r.action_id: r for r in previous.action_results} if previous else {}
        results: list[WorkflowActionResult] = [r for r in prior.values() if r.status == WorkflowActionStatus.SUCCESS]
        succeeded_ids: set[str] = set()
        skipped_ids: set[str] = set()
        stopped = False
        budget = float(get_settings().XNINETZY_TOOL_TIMEOUT_SECONDS)
        if not 0 < budget <= 900:
            raise WorkflowRecoveryError("workflow_invalid_deadline")
        deadline = time.monotonic() + budget

        for action in plan.actions:
            if action.status == WorkflowActionStatus.SUCCESS and action.id in prior:
                succeeded_ids.add(action.id)
                continue
            if time.monotonic() >= deadline:
                raise WorkflowRecoveryError("workflow_deadline_exceeded")
            if self.store:
                from xninetzy.os.policy.action_policy import evaluate_action
                decision = evaluate_action("workflow_resume")
                if not decision.allowed or decision.requires_approval:
                    raise WorkflowRecoveryError("workflow_policy_held")
                if self.store.get(plan.id)["status"] == "cancelled":
                    break
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
                self._persist_action(action, plan, st, results)
                continue

            action.status = WorkflowActionStatus.RUNNING
            action.error = None
            action.result_summary = None
            self._persist_action(action, plan, st, results)
            started = time.monotonic()
            logger.info("workflow_action_started workflow_id=%s action_id=%s type=%s",
                        plan.id, action.id, action.type.value)
            if self.notifier:
                await self._notify("notify_action_started", plan, action)

            result = await execute_action(action, st, self.handlers)
            if result.action_id != action.id or result.status not in {WorkflowActionStatus.SUCCESS, WorkflowActionStatus.FAILED, WorkflowActionStatus.SKIPPED}:
                raise WorkflowRecoveryError("workflow_action_result_invalid")
            result = WorkflowActionResult.model_validate(sanitize_tool_output(result.model_dump(mode="json")))
            result.action_id = action.id
            duration_ms = int((time.monotonic() - started) * 1000)
            action.status = result.status
            action.result_summary = result.summary
            action.error = result.error
            results.append(result)

            if result.status == WorkflowActionStatus.SUCCESS:
                succeeded_ids.add(action.id)
                if result.summary:
                    st.summaries.append(result.summary)
                self._persist_action(action, plan, st, results)
                logger.info(
                    "workflow_action_success workflow_id=%s action_id=%s type=%s duration_ms=%d",
                    plan.id, action.id, action.type.value, duration_ms,
                )
                if self.notifier:
                    await self._notify("notify_action_done", plan, action)
            else:
                logger.info(
                    "workflow_action_failed workflow_id=%s action_id=%s type=%s "
                    "duration_ms=%d critical=%s error_type=%s",
                    plan.id, action.id, action.type.value, duration_ms,
                    action.critical, type(action.error).__name__,
                )
                self._persist_action(action, plan, st, results)
                if self.notifier:
                    await self._notify("notify_action_failed", plan, action)
                if action.critical:
                    stopped = True
                    break

        final_response = self._build_final_response(plan, st, results, stopped)
        overall = (
            WorkflowActionStatus.FAILED if stopped or any(
                result.status != WorkflowActionStatus.SUCCESS for result in results
            )
            else WorkflowActionStatus.SUCCESS
        )
        exec_result = WorkflowExecutionResult(
            plan_id=plan.id, status=overall, final_response=final_response,
            action_results=results,
            checkpoint=WorkflowCheckpoint(plan_hash=plan_fingerprint(plan), state=st),
        )
        if self.store:
            if self.store.get(plan.id)["status"] == "cancelled":
                exec_result.status = WorkflowActionStatus.CANCELLED
                exec_result.final_response = "Workflow dibatalkan; hasil langkah yang sudah selesai tetap tersimpan."
            exec_result = self.store.save_result(plan, exec_result)
        if self.notifier:
            await self._notify("notify_final", plan, self._one_line(plan, results))
        logger.info("workflow_final_synthesis_created workflow_id=%s status=%s",
                    plan.id, overall.value)
        return exec_result

    # ── synthesis ────────────────────────────────────────────────────────────

    def _build_final_response(self, plan, state, results, stopped) -> str:
        # Prefer the FINAL_SYNTHESIS step's output if it ran.
        final = next(
            (r for r in results
             if _is_final(plan, r)
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

    async def _notify(self, method, *args):
        try:
            await getattr(self.notifier, method)(*args)
        except Exception as exc:
            logger.warning("workflow_notification_error type=%s", type(exc).__name__)

    def _persist_action(self, action: WorkflowAction, plan, state, results) -> None:
        if state.plan_id != plan.id or state.chat_id != plan.chat_id or state.original_user_message != plan.original_user_message:
            raise WorkflowRecoveryError("workflow_context_mismatch")
        order = {a.id: index for index, a in enumerate(plan.actions)}
        results.sort(key=lambda r: order[r.action_id])
        if self.store:
            self.store.save_checkpoint(plan, state, results, action)


def _is_final(plan: WorkflowPlan, result: WorkflowActionResult) -> bool:
    for a in plan.actions:
        if a.id == result.action_id:
            return a.type == WorkflowActionType.FINAL_SYNTHESIS
    return False


async def run_workflow(
    chat_id: str, user_message: str, *, context: dict | None = None, from_: bool = True
) -> str:
    """High-level entry: build a plan, execute it, return the final reply text."""
    from xninetzy.workflow.plan import build_workflow_plan

    settings = get_settings()
    plan = await build_workflow_plan(chat_id, user_message, context)
    notifier = (
        WorkflowNotifier(chat_id)
        if (from_ and settings.WORKFLOW_NOTIFY_ENABLED)
        else None
    )
    from xninetzy.workflow.store import WorkflowStore
    store = WorkflowStore()

    state = WorkflowState(
        plan_id=plan.id, chat_id=chat_id, original_user_message=user_message,
        from_=from_,
    )
    executor = WorkflowExecutor(notifier=notifier, store=store)
    result = await executor.execute(plan, state)
    return result.final_response


async def resume_workflow(chat_id: str, workflow_id: str, *, from_: bool = True, handlers=None) -> str:
    """Resume the exact persisted plan; never regenerate from natural language."""
    from xninetzy.workflow.store import WorkflowStore

    store = WorkflowStore()
    try:
        row = store.get(workflow_id)
        if not row or row["chat_id"] != chat_id:
            return "workflow_not_found: workflow tidak ditemukan untuk owner ini."
        plan = WorkflowPlan.model_validate_json(row["plan_json"])
        if plan.id != workflow_id or plan.chat_id != chat_id:
            return "workflow_owner_mismatch: checkpoint tidak sesuai owner atau ID workflow."
    except Exception:
        return "workflow_checkpoint_unavailable: periksa penyimpanan dan checkpoint."
    settings = get_settings()
    notifier = WorkflowNotifier(chat_id) if from_ and settings.WORKFLOW_NOTIFY_ENABLED else None
    result = await WorkflowExecutor(store=store, handlers=handlers, notifier=notifier).execute(plan, resume=True)
    return result.final_response
