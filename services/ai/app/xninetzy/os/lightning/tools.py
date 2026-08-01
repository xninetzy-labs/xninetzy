from __future__ import annotations

import json

from langchain_core.tools import tool

from app.xninetzy.os.lightning.rl import (
    finish_episode,
    list_recent_errors,
    record_action,
    record_outcome,
    reward_summary,
    start_episode,
    strategy_rank,
    regression_check,
)
from app.xninetzy.os.lightning.service import (
    apply_proposal,
    reject_proposal,
    review_recent,
    submit_feedback,
)
from app.xninetzy.os.lightning.store import (
    create_proposal,
    list_proposals,
)


def _uid(sender_id: str | None, chat_id: str | None) -> str:
    return (sender_id or chat_id or "default").strip() or "default"


@tool
def lightning_episode_start(
    task_type: str = "",
    strategy_id: str = "",
    context: dict | None = None,
    interface: str = "mcp",
    idempotency_key: str = "",
    sender_id: str = "",
    chat_id: str = "",
    metadata: dict | None = None,
) -> dict:
    """Mulai episode Lightning owner-scoped."""
    return start_episode(
        owner_scope=_uid(sender_id, chat_id),
        interface=interface or "mcp",
        chat_id=chat_id or None,
        context=context or {},
        strategy_id=strategy_id or None,
        task_type=task_type or None,
        state=metadata or {},
        idempotency_key=idempotency_key or None,
    )


@tool
def lightning_record_action(
    episode_id: str,
    action_type: str,
    action_name: str,
    status: str = "ok",
    input_data: dict | None = None,
    output_data: dict | None = None,
    latency_ms: float | None = None,
    error_type: str = "",
    idempotency_key: str = "",
    sender_id: str = "",
    chat_id: str = "",
) -> dict:
    """Catat action tool atau provider dalam episode."""
    return record_action(
        episode_id=episode_id,
        owner_scope=_uid(sender_id, chat_id),
        action_type=action_type,
        action_name=action_name,
        input_data=input_data or {},
        output_data=output_data or {},
        status=status,
        error_type=error_type or None,
        latency_ms=latency_ms,
        idempotency_key=idempotency_key or None,
    )


@tool
def lightning_record_outcome(
    episode_id: str,
    success: bool,
    outcome_code: str = "",
    evidence_status: str = "",
    latency_ms: float | None = None,
    idempotency_key: str = "",
    sender_id: str = "",
    chat_id: str = "",
) -> dict:
    """Catat outcome dan hitung reward episode."""
    return record_outcome(
        episode_id=episode_id,
        owner_scope=_uid(sender_id, chat_id),
        success=success,
        outcome_code=outcome_code or None,
        evidence_status=evidence_status or None,
        latency_ms=latency_ms,
        idempotency_key=idempotency_key or None,
    )


@tool
def lightning_episode_finish(
    episode_id: str,
    status: str = "completed",
    outcome_code: str = "",
    latency_ms: float | None = None,
    metadata: dict | None = None,
    sender_id: str = "",
    chat_id: str = "",
) -> dict:
    """Finalisasi episode Lightning."""
    return finish_episode(
        episode_id=episode_id,
        owner_scope=_uid(sender_id, chat_id),
        status=status,
        outcome_code=outcome_code or None,
        latency_ms=latency_ms,
        metadata=metadata or {},
    )


@tool
def lightning_feedback(
    feedback_text: str,
    sender_id: str = "",
    chat_id: str = "",
    metadata: dict | None = None,
    episode_id: str = "",
    trace_id: str = "",
    idempotency_key: str = "",
) -> str:
    """Catat feedback user dan hubungkan ke episode."""
    if not feedback_text.strip():
        return "Feedback-nya apa? Contoh: /feedback tadi kepanjangan, harusnya ringkas"
    details = metadata or {}
    return submit_feedback(
        _uid(sender_id, chat_id),
        chat_id or "default",
        feedback_text.strip(),
        details.get("messageId"),
        episode_id=episode_id or None,
        trace_id=trace_id or None,
        idempotency_key=idempotency_key or None,
        source_interface=str(details.get("source", "internal")),
    )


@tool
def lightning_reward_summary(
    window_days: int = 7,
    context_key: str = "",
    sender_id: str = "",
    chat_id: str = "",
) -> dict:
    """Tampilkan ringkasan reward Lightning."""
    return reward_summary(
        owner_scope=_uid(sender_id, chat_id),
        window_days=window_days,
        context_key_value=context_key or None,
    )


@tool
def lightning_strategy_rank(
    context: dict | None = None,
    limit: int = 5,
    sender_id: str = "",
    chat_id: str = "",
) -> dict:
    """Ranking strategy contextual bandit."""
    return strategy_rank(
        owner_scope=_uid(sender_id, chat_id),
        context=context or {},
        limit=limit,
    )


@tool
def lightning_regression_check(
    baseline_strategy_id: str,
    candidate_strategy_id: str,
    window_days: int = 7,
    context_key: str = "",
    sender_id: str = "",
    chat_id: str = "",
) -> dict:
    """Bandingkan baseline dan candidate strategy."""
    return regression_check(
        owner_scope=_uid(sender_id, chat_id),
        baseline_strategy_id=baseline_strategy_id,
        candidate_strategy_id=candidate_strategy_id,
        window_days=window_days,
        context_key_value=context_key or None,
    )


@tool
def lightning_propose_improvement(
    title: str,
    problem: str,
    proposed_change: str,
    target_area: str = "tool_routing",
    risk_level: str = "medium",
    confidence: float = 0.0,
    evidence: dict | None = None,
    patch: dict | None = None,
    sender_id: str = "",
    chat_id: str = "",
    idempotency_key: str = "",
) -> dict:
    """Buat proposal perbaikan Lightning."""
    return create_proposal(
        source_type="lightning",
        source_id=None,
        user_id=_uid(sender_id, chat_id),
        title=title,
        problem=problem,
        proposed_change=proposed_change,
        target_area=target_area,
        risk_level=risk_level,
        confidence=confidence,
        risk_score=0.5 if risk_level == "medium" else 0.8 if risk_level == "high" else 0.2,
        evidence=evidence or {},
        patch=patch or {},
        idempotency_key=idempotency_key or None,
    )


@tool
def lightning_list_proposals() -> str:
    """Tampilkan proposal perbaikan pending."""
    rows = list_proposals(status="pending")
    if not rows:
        return "Tidak ada proposal pending."
    lines = ["*Improvement Proposals (pending)*"]
    for item in rows:
        lines.append(
            f"#{item['id']} [{item['target_area']}/{item['risk_level']}] "
            f"confidence={float(item.get('confidence') or 0):.2f} {item['title']}"
        )
        lines.append(f"   usul: {item['proposed_change']}")
    lines.append("\n/agent-approve <id> · /agent-reject <id>")
    return "\n".join(lines)


@tool
def lightning_improve(sender_id: str = "", chat_id: str = "") -> str:
    """Jalankan review error dan proposal Lightning."""
    return review_recent(_uid(sender_id, chat_id))


@tool
def lightning_approve(
    proposal_id: int,
    sender_id: str | None = None,
    sender_name: str | None = None,
) -> str:
    """Setujui proposal Lightning sebagai admin."""
    return apply_proposal(proposal_id, sender_id, sender_name)


@tool
def lightning_reject(
    proposal_id: int,
    sender_id: str | None = None,
    sender_name: str | None = None,
) -> str:
    """Tolak proposal Lightning sebagai admin."""
    return reject_proposal(proposal_id, sender_id, sender_name)


@tool
def lightning_errors(
    sender_id: str = "",
    chat_id: str = "",
) -> str:
    """Tampilkan error Lightning terbaru."""
    rows = list_recent_errors(owner_scope=_uid(sender_id, chat_id), limit=10)
    if not rows:
        return "Tidak ada error trace terbaru. 👍"
    lines = ["*Recent Agent Errors*"]
    for item in rows:
        lines.append(
            f"• {item.get('error_type') or item.get('outcome_code') or 'error'}: "
            f"{item.get('action_name') or item.get('strategy_id') or ''}"
        )
    return "\n".join(lines)


@tool
def lightning_healthcheck(
    sender_id: str = "",
    chat_id: str = "",
) -> str:
    """Periksa kesehatan Lightning."""
    from app.xninetzy.db.sqlite import connect, init_db
    from app.xninetzy.db.migrations import run_migrations

    init_db()
    run_migrations()
    owner = _uid(sender_id, chat_id)
    with connect() as conn:
        counts = {
            "episodes": conn.execute(
                "SELECT COUNT(*) c FROM agent_episodes WHERE owner_scope=?", (owner,)
            ).fetchone()["c"],
            "actions": conn.execute(
                """
                SELECT COUNT(*) c FROM agent_episode_actions
                WHERE episode_id IN (SELECT episode_id FROM agent_episodes WHERE owner_scope=?)
                """,
                (owner,),
            ).fetchone()["c"],
            "rewards": conn.execute(
                "SELECT COUNT(*) c FROM agent_reward_events WHERE owner_scope=?", (owner,)
            ).fetchone()["c"],
            "feedback": conn.execute(
                "SELECT COUNT(*) c FROM agent_feedback WHERE user_id=?", (owner,)
            ).fetchone()["c"],
            "pending": conn.execute(
                "SELECT COUNT(*) c FROM improvement_proposals WHERE status='pending' AND user_id=?",
                (owner,),
            ).fetchone()["c"],
        }
    summary = reward_summary(owner_scope=owner, window_days=7)
    return json.dumps(
        {
            "status": "ok",
            "owner_scope": owner,
            **counts,
            "window": summary,
            "approval_flow": "owner-only",
            "auto_apply": False,
        },
        ensure_ascii=False,
    )
