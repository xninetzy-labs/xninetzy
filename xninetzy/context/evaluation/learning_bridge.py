from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from xninetzy.context.evaluation.signal_gen import (
    IGNORE,
    LEARN,
    MONITOR,
    LearningSignalBatch,
)
from xninetzy.db.migrations import run_migrations
from xninetzy.db.sqlite import connect


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_db() -> None:
    run_migrations()


@dataclass(frozen=True, slots=True)
class LearningBridgeResult:
    persisted_episode_ids: tuple[str, ...]
    lightning_proposal_ids: tuple[int, ...]
    bandit_episode_ids: tuple[str, ...] = ()


def persist_signal_episodes(
    *,
    cycle_owner: str,
    cycle_id: str,
    batch: LearningSignalBatch,
    related_capabilities: tuple[str, ...] = (),
) -> tuple[str, ...]:
    """Persist LEARN/MONITOR signals as memory_episodes rows so they survive restart."""
    if not batch.signals:
        return ()
    _ensure_db()
    persisted: list[str] = []
    for index, signal in enumerate(batch.signals):
        if signal.action == IGNORE:
            continue
        episode_id = f"signal-{cycle_id}-{index:03d}-{uuid.uuid4().hex[:8]}"
        reward = float(signal.confidence) if signal.action == LEARN else 0.0
        usefulness = float(signal.confidence) if signal.action == MONITOR else 0.5
        task = f"signal:{signal.action}:{signal.source}"
        plan_json = json.dumps(
            [f"cycle={cycle_id}", f"signal_id={episode_id}"],
            ensure_ascii=False,
        )
        actions_json = json.dumps(
            [
                {
                    "source": signal.source,
                    "summary": signal.summary,
                    "evidence_refs": list(signal.evidence_refs),
                    "notes": list(signal.notes),
                    "confidence": float(signal.confidence),
                }
            ],
            ensure_ascii=False,
        )
        with connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO memory_episodes
                  (episode_id, scope, owner, task, intent, plan_json, actions_json,
                   outcome, verification, reward, usefulness, status,
                   related_tools_json, metadata_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    episode_id,
                    "system",
                    cycle_owner,
                    task,
                    f"signal:{signal.action}",
                    plan_json,
                    actions_json,
                    signal.action,
                    "auto-recorded by evaluation layer",
                    reward,
                    usefulness,
                    "active",
                    json.dumps(list(related_capabilities), ensure_ascii=False),
                    json.dumps(
                        {"cycle_id": cycle_id, "source": signal.source},
                        ensure_ascii=False,
                    ),
                    _utcnow(),
                    _utcnow(),
                ),
            )
        persisted.append(episode_id)
    return tuple(persisted)


def create_lightning_proposal_from_cycle(
    *,
    cycle_owner: str,
    cycle_id: str,
    proposal_id_prefix: str,
    title: str,
    problem: str,
    proposed_change: str,
    target_area: str,
    risk_level: str = "medium",
    confidence: float = 0.7,
    baseline_metrics: dict[str, Any] | None = None,
    candidate_metrics: dict[str, Any] | None = None,
    rollback: dict[str, Any] | None = None,
    patch: dict[str, Any] | None = None,
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    """Bridge an evaluation cycle result into a real lightning proposal (DB-persisted)."""
    from xninetzy.os.lightning.store import create_proposal

    return create_proposal(
        source_type="evaluation_cycle",
        source_id=cycle_id,
        user_id=cycle_owner,
        title=title,
        problem=problem,
        proposed_change=proposed_change,
        target_area=target_area,
        patch=patch or {},
        risk_level=risk_level,
        confidence=float(max(0.0, min(1.0, confidence))),
        risk_score=0.5 if risk_level == "medium" else 0.2,
        evidence={
            "cycle_id": cycle_id,
            "proposal_id_prefix": proposal_id_prefix,
        },
        baseline_metrics=baseline_metrics or {},
        candidate_metrics=candidate_metrics or {},
        rollback=rollback or {},
        idempotency_key=idempotency_key or f"cycle:{cycle_id}:{proposal_id_prefix}",
    )


def bridge_cycle_to_learning(
    *,
    cycle_owner: str,
    cycle_id: str,
    batch: LearningSignalBatch,
    error_rate: float,
    block_rate: float,
    overall_quality: float,
    related_capabilities: tuple[str, ...] = (),
    min_failure_rate_to_propose: float = 0.25,
    min_confidence: float = 0.5,
) -> LearningBridgeResult:
    """Persist signals, push LEARN signals to lightning bandit, AND emit lightning proposal on high failure rate."""
    persisted = persist_signal_episodes(
        cycle_owner=cycle_owner,
        cycle_id=cycle_id,
        batch=batch,
        related_capabilities=related_capabilities,
    )
    proposal_ids: list[int] = []
    bandit_episodes: list[str] = []
    for index, signal in enumerate(batch.signals):
        if signal.action != LEARN:
            continue
        try:
            from xninetzy.os.lightning.rl import (
                record_reward_event,
                start_episode,
            )
            episode = start_episode(
                owner_scope=cycle_owner,
                interface="evaluation_bridge",
                chat_id=None,
                context={
                    "cycle_id": cycle_id,
                    "signal_source": signal.source,
                    "capability": signal.summary[:80],
                },
                strategy_id=f"signal:{signal.source}",
                task_type=f"signal:{signal.action}",
                state={"cycle_id": cycle_id, "index": index},
                idempotency_key=f"{cycle_id}:signal:{index}:episode",
            )
            reward_value = max(-1.0, min(1.0, 2.0 * float(signal.confidence) - 1.0))
            record_reward_event(
                episode_id=episode["episode_id"],
                owner_scope=cycle_owner,
                source="evaluation_signal",
                value=reward_value,
                evidence={
                    "signal_source": signal.source,
                    "summary": signal.summary[:200],
                    "confidence": float(signal.confidence),
                    "cycle_id": cycle_id,
                },
                idempotency_key=f"{cycle_id}:signal:{index}:reward",
            )
            bandit_episodes.append(episode["episode_id"])
        except Exception:
            pass
    if (error_rate + block_rate) >= min_failure_rate_to_propose and overall_quality < min_confidence:
        from xninetzy.os.lightning.store import create_proposal

        proposal = create_proposal(
            source_type="evaluation_cycle",
            source_id=cycle_id,
            user_id=cycle_owner,
            title=f"Tune failed capabilities ({cycle_id})",
            problem=(
                f"error_rate={error_rate:.2f} block_rate={block_rate:.2f} "
                f"overall_quality={overall_quality:.2f}"
            ),
            proposed_change=(
                "Investigate failing capabilities and tune routing/policy. "
                "Compare baseline metrics before rollout."
            ),
            target_area="tool_routing",
            patch={"related_capabilities": list(related_capabilities)},
            risk_level="medium",
            confidence=max(0.0, min(1.0, 1.0 - overall_quality)),
            risk_score=0.45,
            evidence={"cycle_id": cycle_id, "failure_rate": error_rate + block_rate},
            baseline_metrics={"overall_quality": overall_quality},
            candidate_metrics={"target_quality": 0.8},
            rollback={"action": "revert_routing", "cycle_id": cycle_id},
            idempotency_key=f"cycle:{cycle_id}:proposal",
        )
        proposal_ids.append(int(proposal["id"]))
    return LearningBridgeResult(
        persisted_episode_ids=persisted,
        lightning_proposal_ids=tuple(proposal_ids),
        bandit_episode_ids=tuple(bandit_episodes),
    )
