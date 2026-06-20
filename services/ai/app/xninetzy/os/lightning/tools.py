from __future__ import annotations

from langchain_core.tools import tool

from app.xninetzy.os.lightning.service import apply_proposal, reject_proposal, review_recent, submit_feedback
from app.xninetzy.os.lightning.store import list_proposals, recent_error_traces


def _uid(sender_id: str | None, chat_id: str | None) -> str:
    return (sender_id or chat_id or "default").strip() or "default"


@tool
def lightning_feedback(feedback_text: str, sender_id: str = "", chat_id: str = "", metadata: dict | None = None) -> str:
    """Catat feedback/koreksi user atas jawaban terakhir; bisa jadi usulan perbaikan."""
    if not feedback_text.strip():
        return "Feedback-nya apa? Contoh: `/feedback tadi kepanjangan, harusnya ringkas`"
    msg_id = (metadata or {}).get("messageId")
    return submit_feedback(_uid(sender_id, chat_id), chat_id or "default", feedback_text.strip(), msg_id)


@tool
def lightning_list_proposals() -> str:
    """Tampilkan usulan perbaikan (improvement proposals) yang pending."""
    rows = list_proposals(status="pending")
    if not rows:
        return "Tidak ada proposal pending."
    lines = ["*Improvement Proposals (pending)*"]
    for p in rows:
        lines.append(f"#{p['id']} [{p['target_area']}/{p['risk_level']}] {p['title']}")
        lines.append(f"   usul: {p['proposed_change']}")
    lines.append("\n`/agent-approve <id>` · `/agent-reject <id>`")
    return "\n".join(lines)


@tool
def lightning_improve(sender_id: str = "", chat_id: str = "") -> str:
    """Jalankan review Lightning: mining error berulang + ringkasan proposal pending."""
    return review_recent(_uid(sender_id, chat_id))


@tool
def lightning_approve(proposal_id: int, sender_id: str | None = None, sender_name: str | None = None) -> str:
    """Setujui & terapkan improvement proposal (admin only)."""
    return apply_proposal(proposal_id, sender_id, sender_name)


@tool
def lightning_reject(proposal_id: int, sender_id: str | None = None, sender_name: str | None = None) -> str:
    """Tolak improvement proposal (admin only)."""
    return reject_proposal(proposal_id, sender_id, sender_name)


@tool
def lightning_errors() -> str:
    """Tampilkan trace error terbaru."""
    rows = recent_error_traces(limit=10)
    if not rows:
        return "Tidak ada error trace terbaru. 👍"
    lines = ["*Recent Agent Errors*"]
    for t in rows:
        lines.append(f"• {t.get('error_type') or 'error'}: {(t.get('error_message') or '')[:80]}")
    return "\n".join(lines)


@tool
def lightning_healthcheck() -> str:
    """Healthcheck Lightning self-improvement (untuk /test-lightning)."""
    from app.xninetzy.db.sqlite import connect, init_db

    init_db()
    with connect() as conn:
        traces = conn.execute("SELECT COUNT(*) c FROM agent_traces").fetchone()["c"]
        fb = conn.execute("SELECT COUNT(*) c FROM agent_feedback").fetchone()["c"]
        pend = conn.execute("SELECT COUNT(*) c FROM improvement_proposals WHERE status='pending'").fetchone()["c"]
    return (
        "*Lightning Healthcheck*\n"
        "• Trace logger: OK\n"
        f"• Traces tercatat: {traces}\n"
        f"• Feedback tercatat: {fb}\n"
        f"• Proposal pending: {pend}\n"
        "• Approval flow: OK (admin-only)"
    )
