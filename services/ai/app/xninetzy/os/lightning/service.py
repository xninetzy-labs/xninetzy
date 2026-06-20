from __future__ import annotations

from collections import Counter

from app.xninetzy.os.lightning.feedback_parser import classify_feedback
from app.xninetzy.os.lightning.store import (
    create_proposal,
    get_proposal,
    latest_trace,
    list_proposals,
    log_feedback,
    recent_error_traces,
    set_proposal_status,
)
from app.xninetzy.os.research.permissions import is_owner_admin


def submit_feedback(user_id: str, chat_id: str, feedback_text: str, message_id: str | None = None) -> str:
    """Record feedback; if it implies a behavior change, open an improvement proposal."""
    parsed = classify_feedback(feedback_text)
    trace = latest_trace(chat_id)
    fid = log_feedback(
        user_id=user_id, chat_id=chat_id, message_id=message_id,
        trace_id=(trace or {}).get("trace_id"),
        feedback_type=parsed["feedback_type"], feedback_text=feedback_text,
        severity=parsed["severity"], parsed_issue=parsed,
    )

    if parsed["feedback_type"] == "praise":
        return "🙏 Makasih feedback-nya, dicatat."

    if parsed["implies_change"] and parsed["suggested_rule"]:
        prop = create_proposal(
            source_type="feedback", source_id=fid, user_id=user_id,
            title=f"Rule dari feedback: {parsed['suggested_rule'][:50]}",
            problem=feedback_text,
            proposed_change=parsed["suggested_rule"],
            target_area="rule",
            patch={"rule_content": parsed["suggested_rule"], "user_id": user_id},
            risk_level="low",
        )
        return (
            "📝 Feedback dicatat dan dibuatkan usulan perbaikan:\n\n"
            f"*Proposal #{prop['id']}* — tambah aturan:\n“{parsed['suggested_rule']}”\n\n"
            f"Setujui: `/agent-approve {prop['id']}`  ·  tolak: `/agent-reject {prop['id']}`"
        )
    return "📝 Feedback dicatat. Belum ada perubahan otomatis yang diusulkan."


def review_recent(user_id: str) -> str:
    """Heuristic review: mine recurring errors into proposals + summarize pending."""
    errors = recent_error_traces(limit=30)
    created: list[str] = []
    if errors:
        by_type = Counter((e.get("error_type") or "unknown") for e in errors)
        existing = {p["proposed_change"] for p in list_proposals(status=None, limit=100)}
        for err_type, count in by_type.items():
            if count < 2:
                continue
            change = f"Tangani error berulang '{err_type}' ({count}x) dengan guard/handler"
            if change in existing:
                continue
            prop = create_proposal(
                source_type="error", source_id=err_type, user_id=user_id,
                title=f"Error berulang: {err_type}", problem=f"{count} trace gagal dengan {err_type}",
                proposed_change=change, target_area="tool_routing", patch={"error_type": err_type},
                risk_level="medium",
            )
            created.append(f"#{prop['id']} {prop['title']}")

    pending = list_proposals(status="pending", limit=20)
    lines = ["*Lightning Agent Review*\n"]
    lines.append(f"Error traces dianalisis: {len(errors)}")
    if created:
        lines.append("\nProposal baru dari error:")
        lines.extend(f"• {c}" for c in created)
    if pending:
        lines.append("\n*Proposal Pending*")
        for p in pending:
            lines.append(f"#{p['id']} [{p['target_area']}/{p['risk_level']}] {p['title']}")
        lines.append("\n`/agent-approve <id>` · `/agent-reject <id>`")
    else:
        lines.append("\nTidak ada proposal pending. 👍")
    return "\n".join(lines)


def apply_proposal(proposal_pk: int, sender_id: str | None, sender_name: str | None) -> str:
    if not is_owner_admin(sender_id, sender_name):
        return "Maaf, approve/reject proposal hanya untuk admin."
    p = get_proposal(proposal_pk)
    if not p:
        return f"Proposal #{proposal_pk} tidak ditemukan."
    if p["status"] != "pending":
        return f"Proposal #{proposal_pk} sudah berstatus {p['status']}."

    import json

    patch = {}
    try:
        patch = json.loads(p.get("patch_json") or "{}")
    except Exception:
        patch = {}

    applied_note = "status diperbarui (belum ada auto-apply untuk area ini)."
    if p["target_area"] == "rule" and patch.get("rule_content"):
        from app.xninetzy.os.rules.store import add_rule

        rule_user = patch.get("user_id") or p.get("user_id") or "default"
        r = add_rule(rule_user, patch["rule_content"], priority=60)
        applied_note = f"aturan baru #{r['id']} ditambahkan: “{patch['rule_content']}”"

    set_proposal_status(proposal_pk, "approved", reviewed_by=sender_name or sender_id)
    return f"✅ Proposal #{proposal_pk} disetujui — {applied_note}"


def reject_proposal(proposal_pk: int, sender_id: str | None, sender_name: str | None) -> str:
    if not is_owner_admin(sender_id, sender_name):
        return "Maaf, approve/reject proposal hanya untuk admin."
    p = get_proposal(proposal_pk)
    if not p:
        return f"Proposal #{proposal_pk} tidak ditemukan."
    if p["status"] != "pending":
        return f"Proposal #{proposal_pk} sudah berstatus {p['status']}."
    set_proposal_status(proposal_pk, "rejected", reviewed_by=sender_name or sender_id)
    return f"✅ Proposal #{proposal_pk} ditolak."
