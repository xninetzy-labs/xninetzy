from __future__ import annotations

from langchain_core.tools import tool

from app.xninetzy.os.hitl.approval_service import get_approval_status, list_pending, request_approval, set_approval_status


@tool
def hitl_request_approval(
    action_type: str,
    title: str,
    summary: str,
    chat_id: str = "system",
    sender_id: str | None = None,
    payload: dict | None = None,
) -> str:
    """Buat approval request untuk aksi berdampak besar."""
    approval_id = request_approval(chat_id, sender_id, action_type, title, summary, payload)
    return (
        f"*Approval Required #{approval_id}*\n\n"
        f"*Tipe:* {action_type}\n"
        f"*Judul:* {title}\n\n"
        f"{summary}\n\n"
        f"Balas:\n`/approve {approval_id}`\natau\n`/reject {approval_id}`"
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
