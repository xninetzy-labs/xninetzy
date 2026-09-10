from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime

from app.xninetzy.os.lightning.feedback_parser import classify_feedback
from app.xninetzy.os.lightning.rl import record_feedback_event
from app.xninetzy.os.lightning.store import (
    create_proposal,
    get_proposal,
    list_proposals,
    log_feedback,
    recent_error_traces,
    set_proposal_status,
    trace_for_message,
)
from app.xninetzy.os.research.permissions import is_owner_admin


def submit_feedback(
    user_id: str,
    chat_id: str,
    feedback_text: str,
    message_id: str | None = None,
    *,
    episode_id: str | None = None,
    trace_id: str | None = None,
    idempotency_key: str | None = None,
    source_interface: str = "internal",
) -> str:
    parsed = classify_feedback(feedback_text)
    trace = trace_for_message(
        chat_id=chat_id,
        message_id=message_id,
        trace_id=trace_id,
    )
    attribution = "explicit" if episode_id or trace_id or message_id else "low"
    resolved_trace_id = trace_id or (trace or {}).get("trace_id")
    fid = log_feedback(
        user_id=user_id,
        chat_id=chat_id,
        message_id=message_id,
        trace_id=resolved_trace_id,
        feedback_type=parsed["feedback_type"],
        feedback_text=feedback_text,
        severity=parsed["severity"],
        parsed_issue=parsed,
        episode_id=episode_id,
        idempotency_key=idempotency_key,
        source_interface=source_interface,
        attribution_confidence=attribution,
    )

    if episode_id:
        record_feedback_event(
            episode_id=episode_id,
            owner_scope=user_id,
            feedback_type=parsed["feedback_type"],
            feedback_text=feedback_text,
            idempotency_key=idempotency_key or f"{fid}:reward",
        )

    if parsed["feedback_type"] == "praise":
        return "🙏 Makasih feedback-nya, dicatat."

    if parsed["implies_change"] and parsed["suggested_rule"]:
        prop = create_proposal(
            source_type="feedback",
            source_id=fid,
            user_id=user_id,
            title=f"Rule dari feedback: {parsed['suggested_rule'][:50]}",
            problem=feedback_text,
            proposed_change=parsed["suggested_rule"],
            target_area="rule",
            patch={"rule_content": parsed["suggested_rule"], "user_id": user_id},
            risk_level="low",
            confidence=0.75 if attribution == "explicit" else 0.45,
            risk_score=0.15,
            evidence={"feedback_id": fid, "attribution": attribution},
            idempotency_key=f"{fid}:proposal",
        )
        return (
            "📝 Feedback dicatat dan dibuatkan usulan perbaikan:\n\n"
            f"Proposal #{prop['id']} — tambah aturan:\n“{parsed['suggested_rule']}”\n\n"
            f"Setujui: /agent-approve {prop['id']} · tolak: /agent-reject {prop['id']}"
        )
    return "📝 Feedback dicatat. Belum ada perubahan otomatis yang diusulkan."


def review_recent(user_id: str) -> str:
    errors = recent_error_traces(limit=30)
    created: list[str] = []
    if errors:
        by_type = Counter((item.get("error_type") or "unknown") for item in errors)
        existing = {item["proposed_change"] for item in list_proposals(status=None, limit=100)}
        for error_type, count in by_type.items():
            if count < 2:
                continue
            change = f"Tangani error berulang '{error_type}' ({count}x) dengan guard/handler"
            if change in existing:
                continue
            prop = create_proposal(
                source_type="error",
                source_id=error_type,
                user_id=user_id,
                title=f"Error berulang: {error_type}",
                problem=f"{count} trace gagal dengan {error_type}",
                proposed_change=change,
                target_area="tool_routing",
                patch={"error_type": error_type},
                risk_level="medium",
                confidence=min(0.95, 0.45 + count / 20),
                risk_score=0.45,
                evidence={"error_count": count},
                idempotency_key=f"error:{error_type}:{count}",
            )
            created.append(f"#{prop['id']} {prop['title']}")

    pending = list_proposals(status="pending", limit=20)
    lines = ["*Lightning Agent Review*\n"]
    lines.append(f"Error traces dianalisis: {len(errors)}")
    if created:
        lines.append("\nProposal baru dari error:")
        lines.extend(f"• {item}" for item in created)
    if pending:
        lines.append("\n*Proposal Pending*")
        for item in pending:
            lines.append(
                f"#{item['id']} [{item['target_area']}/{item['risk_level']}] "
                f"confidence={float(item.get('confidence') or 0):.2f} {item['title']}"
            )
        lines.append("\n/agent-approve <id> · /agent-reject <id>")
    else:
        lines.append("\nTidak ada proposal pending. 👍")
    return "\n".join(lines)


def apply_proposal(
    proposal_pk: int,
    sender_id: str | None,
    sender_name: str | None,
) -> str:
    if not is_owner_admin(sender_id, sender_name):
        return "Maaf, approve/reject proposal hanya untuk admin."
    proposal = get_proposal(proposal_pk)
    if not proposal:
        return f"Proposal #{proposal_pk} tidak ditemukan."
    if proposal["status"] != "pending":
        return f"Proposal #{proposal_pk} sudah berstatus {proposal['status']}."
    expires_at = proposal.get("expires_at")
    if expires_at:
        try:
            if datetime.fromisoformat(expires_at) <= datetime.now(UTC):
                set_proposal_status(proposal_pk, "expired", sender_name or sender_id)
                return f"Proposal #{proposal_pk} sudah kedaluwarsa."
        except ValueError:
            pass

    import json

    try:
        patch = json.loads(proposal.get("patch_json") or "{}")
    except Exception:
        patch = {}

    applied_note = "status diperbarui; area ini memerlukan implementasi manual."
    rollout_state = "approved"
    if proposal["target_area"] == "rule" and patch.get("rule_content"):
        from app.xninetzy.os.rules.store import add_rule

        rule_user = patch.get("user_id") or proposal.get("user_id") or "default"
        rule = add_rule(rule_user, patch["rule_content"], priority=60)
        applied_note = f"aturan baru #{rule['id']} ditambahkan: “{patch['rule_content']}”"
        rollout_state = "active"

    set_proposal_status(
        proposal_pk,
        "approved",
        reviewed_by=sender_name or sender_id,
        rollout_state=rollout_state,
    )
    return f"✅ Proposal #{proposal_pk} disetujui — {applied_note}"


def reject_proposal(
    proposal_pk: int,
    sender_id: str | None,
    sender_name: str | None,
) -> str:
    if not is_owner_admin(sender_id, sender_name):
        return "Maaf, approve/reject proposal hanya untuk admin."
    proposal = get_proposal(proposal_pk)
    if not proposal:
        return f"Proposal #{proposal_pk} tidak ditemukan."
    if proposal["status"] != "pending":
        return f"Proposal #{proposal_pk} sudah berstatus {proposal['status']}."
    set_proposal_status(
        proposal_pk,
        "rejected",
        reviewed_by=sender_name or sender_id,
        rollout_state="rejected",
    )
    return f"✅ Proposal #{proposal_pk} ditolak."
