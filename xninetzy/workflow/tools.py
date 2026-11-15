"""-facing tools for inspecting / resuming / cancelling workflows."""

from __future__ import annotations

from langchain_core.tools import tool

from xninetzy.core.logging import logging
from xninetzy.workflow.models import WorkflowPlan

logger = logging.getLogger(__name__)

_STATUS_ICON = {
    "success": "✅", "failed": "⚠️", "skipped": "⏭️",
    "running": "⏳", "pending": "•", "cancelled": "🚫",
}


def _format_run(row: dict) -> str:
    lines = [f"🧭 *Workflow* `{row['id'][:8]}` — {row.get('status', '?')}"]
    if row.get("title"):
        lines.append(f"_{row['title']}_")
    try:
        plan = WorkflowPlan.model_validate_json(row["plan_json"])
        for i, a in enumerate(plan.actions, 1):
            icon = _STATUS_ICON.get(a.status.value, "•")
            extra = f" — {a.result_summary}" if a.result_summary else (f" — {a.error}" if a.error else "")
            lines.append(f"{icon} {i}. {a.title}{extra}"[:160])
    except Exception:
        pass
    return "\n".join(lines)


@tool
async def workflow_status(chat_id: str, workflow_id: str | None = None) -> str:
    """Tampilkan status workflow (default: workflow terbaru) beserta tiap langkahnya.

    Args:
        chat_id: Chat  (dari context).
        workflow_id: ID workflow tertentu (opsional).
    """
    from xninetzy.workflow.store import WorkflowStore
    store = WorkflowStore()
    row = store.get(workflow_id) if workflow_id else store.get_latest(chat_id)
    if not row or row.get("chat_id") != chat_id:
        return "Belum ada workflow untuk chat ini."
    return _format_run(row)


@tool
async def workflow_latest(chat_id: str) -> str:
    """Tampilkan workflow terakhir yang dijalankan di chat ini."""
    return await workflow_status.ainvoke({"chat_id": chat_id})


@tool
async def workflow_resume(chat_id: str, workflow_id: str) -> str:
    """Lanjutkan checkpoint workflow dengan ID yang sama tanpa mengulang langkah sukses.

    Args:
        chat_id: Chat  (dari context).
        workflow_id: ID workflow yang mau dilanjutkan.
    """
    from xninetzy.workflow.store import WorkflowStore
    from xninetzy.workflow.executor import resume_workflow
    store = WorkflowStore()
    row = store.get(workflow_id)
    if not row or row.get("chat_id") != chat_id:
        return f"Workflow `{workflow_id}` tidak ditemukan untuk chat ini."
    logger.info("workflow_resume workflow_id=%s", workflow_id)
    return await resume_workflow(chat_id, workflow_id, from_=True)


@tool
async def workflow_cancel(chat_id: str, workflow_id: str) -> str:
    """Batalkan workflow berjalan, pending, atau gagal agar tidak dilanjutkan."""
    from xninetzy.workflow.store import WorkflowStore
    store = WorkflowStore()
    ok = store.mark_cancelled(chat_id, workflow_id)
    return (
        f"🚫 Workflow `{workflow_id[:8]}` dibatalkan."
        if ok
        else f"Workflow `{workflow_id}` tidak bisa dibatalkan (mungkin sudah selesai)."
    )
