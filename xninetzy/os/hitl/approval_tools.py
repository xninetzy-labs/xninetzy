from __future__ import annotations

from langchain_core.tools import tool

from xninetzy.os.hitl.approval_service import get_approval_status, list_pending, request_approval, set_approval_status
from xninetzy.os.notifications.admin_notifier import notify_admin_approval
from xninetzy.os.policy.action_policy import evaluate_action


@tool
async def hitl_request_plan_approval(
    plan_id: str,
    final_steps: list[str],
    title: str = "",
    summary: str = "",
    chat_id: str = "system",
    sender_id: str | None = None,
    payload: dict | None = None,
) -> str:
    """Buat satu approval yang mencakup banyak langkah FINAL dalam satu plan.

    Args:
        plan_id: Identifier plan harness.
        final_steps: Daftar step_id ber-risk FINAL yang dicakup.
        title: Judul ringkas.
        summary: Ringkasan rencana + dampak.
        chat_id: Chat ID.
        sender_id: Owner principal.
        payload: Dict payload tambahan.
    """
    bounded_steps = [str(step).strip() for step in (final_steps or []) if str(step).strip()]
    if not bounded_steps:
        return "Tidak ada final_steps; gunakan hitl_request_approval untuk satu aksi."
    enriched_payload = dict(payload or {})
    enriched_payload["plan_id"] = plan_id
    enriched_payload["final_steps"] = bounded_steps
    composed_title = title.strip() or f"Plan approval: {plan_id}"
    composed_summary = summary.strip() or (
        f"Plan `{plan_id}` memiliki {len(bounded_steps)} langkah FINAL:\n"
        + "\n".join(f"- {step}" for step in bounded_steps)
    )
    decision = evaluate_action("plan_approval", enriched_payload)
    if not decision.allowed:
        return f"Aksi `plan_approval` harus dilakukan manual oleh owner: {decision.reason}"
    approval_id = request_approval(
        chat_id,
        sender_id,
        "plan_approval",
        composed_title,
        composed_summary,
        enriched_payload,
    )
    delivered = await notify_admin_approval(
        approval_id,
        "plan_approval",
        composed_title,
        composed_summary,
    )
    delivery = (
        "Tombol approve/reject sudah dikirim ke WhatsApp admin."
        if delivered
        else "Tombol gagal dikirim; periksa ADMIN_JID dan koneksi WA Engine."
    )
    return (
        f"*Plan Approval Required #{approval_id}*\n\n"
        f"*Plan:* {plan_id}\n"
        f"*Policy:* {decision.mode.value} ({decision.risk.value})\n"
        f"*Steps:* {len(bounded_steps)}\n\n"
        f"{composed_summary}\n\n"
        f"{delivery}\n\n"
        f"Fallback:\n`/approve {approval_id}`\natau\n`/reject {approval_id}`"
    )


@tool
async def hitl_request_approval(
    action_type: str,
    title: str,
    summary: str,
    chat_id: str = "system",
    sender_id: str | None = None,
    payload: dict | None = None,
) -> str:
    """Buat approval request untuk aksi berdampak besar."""
    decision = evaluate_action(action_type, payload)
    if not decision.allowed:
        return f"Aksi `{action_type}` harus dilakukan manual oleh owner: {decision.reason}"
    approval_id = request_approval(chat_id, sender_id, action_type, title, summary, payload)
    delivered = await notify_admin_approval(
        approval_id,
        action_type,
        title,
        summary,
    )
    delivery = (
        "Tombol approve/reject sudah dikirim ke WhatsApp admin."
        if delivered
        else "Tombol gagal dikirim; periksa ADMIN_JID dan koneksi WA Engine."
    )
    return (
        f"*Approval Required #{approval_id}*\n\n"
        f"*Tipe:* {action_type}\n"
        f"*Policy:* {decision.mode.value} ({decision.risk.value})\n\n"
        f"*Judul:* {title}\n\n"
        f"{summary}\n\n"
        f"{delivery}\n\n"
        f"Fallback:\n`/approve {approval_id}`\natau\n`/reject {approval_id}`"
    )


@tool
def hitl_list_pending() -> str:
    """List approval pending."""
    rows = list_pending()
    if not rows:
        return "Tidak ada approval pending."
    lines = ["*Approval Pending*"]
    for row in rows:
        lines.append(f"#{row['id']} - {row['title']}")
        lines.append(f"  Tipe: {row['action_type']}")
    return "\n".join(lines)


@tool
def hitl_approve(approval_id: int, sender_id: str | None = None, sender_name: str | None = None) -> str:
    """Approve request. Hanya admin."""
    _, message = set_approval_status(approval_id, "approved", sender_id, sender_name)
    return message


@tool
def hitl_reject(approval_id: int, sender_id: str | None = None, sender_name: str | None = None) -> str:
    """Reject request. Hanya admin."""
    _, message = set_approval_status(approval_id, "rejected", sender_id, sender_name)
    return message


@tool
def hitl_get_status(approval_id: int) -> str:
    """Cek status approval."""
    row = get_approval_status(approval_id)
    if not row:
        return f"Approval #{approval_id} tidak ditemukan."
    return f"Approval #{approval_id}: *{row['status']}*\n{row['title']}"
