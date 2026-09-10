from __future__ import annotations

import hashlib
import json
import math
import re
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from app.xninetzy.core.config import get_settings
from app.xninetzy.db.migrations import run_migrations
from app.xninetzy.db.sqlite import connect, init_db


_SENSITIVE_RE = re.compile(
    r"(?i)(api[_-]?key|access[_-]?token|bearer|password|passwd|secret|cookie|"
    r"storage[_-]?state|captcha)(\\s*[:=]\\s*)([^,;\\s]+)"
)
_SOURCE_WEIGHTS = {
    "task_success": 0.30,
    "user_feedback": 0.25,
    "evidence_quality": 0.25,
    "tool_reliability": 0.15,
    "latency": 0.05,
}
_SOURCE_ALIASES = {"groundedness": "evidence_quality"}


def _now() -> str:
    return datetime.now(ZoneInfo(get_settings().APP_TIMEZONE)).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def _clamp(value: float) -> float:
    return max(-1.0, min(1.0, float(value)))


def _redact(value: Any, depth: int = 0) -> Any:
    if depth > 4:
        return "[truncated]"
    if isinstance(value, dict):
        return {str(key): _redact(item, depth + 1) for key, item in value.items()}
    if isinstance(value, list):
        return [_redact(item, depth + 1) for item in value[:50]]
    if isinstance(value, tuple):
        return [_redact(item, depth + 1) for item in value[:50]]
    if value is None or isinstance(value, (bool, int, float)):
        return value
    text = str(value)[: int(getattr(get_settings(), "LIGHTNING_MAX_EVENT_CHARS", 4000))]
    return _SENSITIVE_RE.sub(r"\\1[redacted]", text)


def _json(value: Any) -> str:
    return json.dumps(_redact(value), ensure_ascii=False, sort_keys=True, default=str)


def _owner(owner_scope: str | None) -> str:
    return (owner_scope or "default").strip() or "default"


def context_key(
    *,
    domain: str = "",
    intent: str = "",
    modality: str = "text",
    risk_class: str = "read",
    task_type: str = "",
) -> str:
    parts = [
        re.sub(r"[^a-z0-9_-]+", "-", str(value).lower()).strip("-")
        for value in (domain, intent, modality, risk_class, task_type)
    ]
    normalized = ":".join(part or "unknown" for part in parts)
    return normalized[:240]


def strategy_key(
    *,
    route: str = "",
    provider: str = "",
    model: str = "",
    retrieval_policy: str = "",
    skill_ids: list[str] | None = None,
    tool_order_version: str = "v1",
) -> str:
    skills = ",".join(sorted(str(item) for item in (skill_ids or [])))
    value = "|".join(
        (
            route or "default",
            provider or "default",
            model or "default",
            retrieval_policy or "default",
            skills or "none",
            tool_order_version or "v1",
        )
    )
    return value[:500]


def _ensure() -> None:
    init_db()
    run_migrations()


def start_episode(
    *,
    owner_scope: str,
    interface: str = "internal",
    chat_id: str | None = None,
    message_id: str | None = None,
    trace_id: str | None = None,
    context: dict[str, Any] | None = None,
    strategy_id: str | None = None,
    task_type: str | None = None,
    provider: str | None = None,
    model: str | None = None,
    skill_ids: list[str] | None = None,
    state: dict[str, Any] | None = None,
    idempotency_key: str | None = None,
) -> dict:
    _ensure()
    owner = _owner(owner_scope)
    context_data = context or {}
    ctx = context_key(
        domain=str(context_data.get("domain", "")),
        intent=str(context_data.get("intent", "")),
        modality=str(context_data.get("modality", "text")),
        risk_class=str(context_data.get("risk_class", "read")),
        task_type=task_type or str(context_data.get("task_type", "")),
    )
    strategy = strategy_id or strategy_key(
        route=str(context_data.get("route", "default")),
        provider=provider or "",
        model=model or "",
        retrieval_policy=str(context_data.get("retrieval_policy", "")),
        skill_ids=skill_ids,
    )
    with connect() as conn:
        if idempotency_key:
            existing = conn.execute(
                "SELECT * FROM agent_episodes WHERE owner_scope=? AND idempotency_key=?",
                (owner, idempotency_key),
            ).fetchone()
            if existing:
                return dict(existing)
        episode_id = _id("E")
        now = _now()
        try:
            conn.execute(
                """
                INSERT INTO agent_episodes
                (episode_id, owner_scope, interface, chat_id, message_id, trace_id,
                 context_key, strategy_id, task_type, provider, model,
                 skill_ids_json, state_json, status, started_at, metadata_json,
                 idempotency_key)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    episode_id,
                    owner,
                    interface or "internal",
                    chat_id,
                    message_id,
                    trace_id,
                    ctx,
                    strategy,
                    task_type,
                    provider,
                    model,
                    _json(skill_ids or []),
                    _json(state or {}),
                    "active",
                    now,
                    _json({"source": interface or "internal"}),
                    idempotency_key,
                ),
            )
        except Exception:
            if not idempotency_key:
                raise
            existing = conn.execute(
                "SELECT * FROM agent_episodes WHERE owner_scope=? AND idempotency_key=?",
                (owner, idempotency_key),
            ).fetchone()
            if not existing:
                raise
            return dict(existing)
    return {
        "episode_id": episode_id,
        "owner_scope": owner,
        "interface": interface or "internal",
        "context_key": ctx,
        "strategy_id": strategy,
        "status": "active",
        "started_at": now,
    }


def get_episode(episode_id: str, owner_scope: str) -> dict | None:
    _ensure()
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM agent_episodes WHERE episode_id=? AND owner_scope=?",
            (episode_id, _owner(owner_scope)),
        ).fetchone()
    return dict(row) if row else None


def record_action(
    *,
    episode_id: str,
    owner_scope: str,
    action_type: str,
    action_name: str,
    input_data: Any = None,
    output_data: Any = None,
    status: str = "ok",
    error_type: str | None = None,
    latency_ms: float | None = None,
    idempotency_key: str | None = None,
) -> dict:
    _ensure()
    owner = _owner(owner_scope)
    with connect() as conn:
        episode = conn.execute(
            "SELECT * FROM agent_episodes WHERE episode_id=? AND owner_scope=?",
            (episode_id, owner),
        ).fetchone()
        if not episode:
            raise ValueError("Episode tidak ditemukan atau bukan milik owner.")
        if idempotency_key:
            existing = conn.execute(
                "SELECT * FROM agent_episode_actions WHERE episode_id=? AND idempotency_key=?",
                (episode_id, idempotency_key),
            ).fetchone()
            if existing:
                return dict(existing)
        ordinal = conn.execute(
            "SELECT COALESCE(MAX(ordinal), 0) + 1 AS next_ordinal FROM agent_episode_actions WHERE episode_id=?",
            (episode_id,),
        ).fetchone()["next_ordinal"]
        action_id = _id("A")
        conn.execute(
            """
            INSERT INTO agent_episode_actions
            (action_id, episode_id, ordinal, action_type, action_name,
             input_json, output_json, status, error_type, latency_ms, idempotency_key, created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                action_id,
                episode_id,
                ordinal,
                action_type or "tool",
                action_name,
                _json({"idempotency_key": idempotency_key, "input": input_data}),
                _json(output_data or {}),
                status or "ok",
                error_type,
                latency_ms,
                idempotency_key,
                _now(),
            ),
        )
    return {
        "action_id": action_id,
        "episode_id": episode_id,
        "ordinal": ordinal,
        "status": status or "ok",
    }


def record_reward_event(
    *,
    episode_id: str,
    owner_scope: str,
    source: str,
    value: float,
    evidence: dict[str, Any] | None = None,
    idempotency_key: str | None = None,
) -> dict:
    _ensure()
    owner = _owner(owner_scope)
    bounded = _clamp(value)
    with connect() as conn:
        episode = conn.execute(
            "SELECT episode_id FROM agent_episodes WHERE episode_id=? AND owner_scope=?",
            (episode_id, owner),
        ).fetchone()
        if not episode:
            raise ValueError("Episode tidak ditemukan atau bukan milik owner.")
        if idempotency_key:
            existing = conn.execute(
                "SELECT * FROM agent_reward_events WHERE owner_scope=? AND idempotency_key=?",
                (owner, idempotency_key),
            ).fetchone()
            if existing:
                return dict(existing)
        event_id = _id("R")
        try:
            conn.execute(
                """
                INSERT INTO agent_reward_events
                (event_id, episode_id, owner_scope, source, value, evidence_json,
                 idempotency_key, created_at)
                VALUES (?,?,?,?,?,?,?,?)
                """,
                (
                    event_id,
                    episode_id,
                    owner,
                    source,
                    bounded,
                    _json(evidence or {}),
                    idempotency_key,
                    _now(),
                ),
            )
        except Exception:
            if not idempotency_key:
                raise
            existing = conn.execute(
                "SELECT * FROM agent_reward_events WHERE owner_scope=? AND idempotency_key=?",
                (owner, idempotency_key),
            ).fetchone()
            if not existing:
                raise
            return dict(existing)
    return {
        "event_id": event_id,
        "episode_id": episode_id,
        "source": source,
        "value": bounded,
    }


def _reward_for(conn, episode_id: str) -> tuple[float, dict, dict]:
    rows = conn.execute("SELECT source, value FROM agent_reward_events WHERE episode_id=? ORDER BY id", (episode_id,)).fetchall()
    totals: dict[str, list[float]] = {}
    for row in rows:
        source = _SOURCE_ALIASES.get(row["source"], row["source"])
        totals.setdefault(source, []).append(float(row["value"]))
    components = {
        source: sum(values) / len(values)
        for source, values in totals.items()
    }
    action_counts = conn.execute("SELECT COUNT(*) total, SUM(CASE WHEN status='ok' THEN 1 ELSE 0 END) ok_count FROM agent_episode_actions WHERE episode_id=?", (episode_id,)).fetchone()
    if action_counts["total"] and "tool_reliability" not in components:
        total = int(action_counts["total"])
        components["tool_reliability"] = _clamp((2 * int(action_counts["ok_count"] or 0) / total) - 1)
    coverage = sum(_SOURCE_WEIGHTS[source] for source in components if source in _SOURCE_WEIGHTS)
    weighted = 0.0
    for source, value in components.items():
        weighted += _SOURCE_WEIGHTS.get(source, 0.0) * _clamp(value)
    missing = sorted(source for source in _SOURCE_WEIGHTS if source not in components)
    reward = _clamp(weighted)
    quality = {"coverage": round(coverage, 6), "confidence": round(coverage, 6), "missing_components": missing, "reward_version": "v2"}
    return reward, components, quality


def finish_episode(
    *,
    episode_id: str,
    owner_scope: str,
    status: str,
    outcome_code: str | None = None,
    latency_ms: float | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict:
    _ensure()
    owner = _owner(owner_scope)
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM agent_episodes WHERE episode_id=? AND owner_scope=?",
            (episode_id, owner),
        ).fetchone()
        if not row:
            raise ValueError("Episode tidak ditemukan atau bukan milik owner.")
        if row["status"] != "active":
            return dict(row)
        reward, components, quality = _reward_for(conn, episode_id)
        completed_at = _now()
        conn.execute(
            """
            UPDATE agent_episodes
            SET status=?, outcome_code=?, completed_at=?, latency_ms=?,
                reward=?, reward_breakdown_json=?, metadata_json=?
            WHERE episode_id=? AND owner_scope=?
            """,
            (
                status or "completed",
                outcome_code,
                completed_at,
                latency_ms,
                reward,
                _json({"total": reward, "components": components, **quality}),
                _json(metadata or {}),
                episode_id,
                owner,
            ),
        )
        action_stats = conn.execute(
            """
            SELECT
              COUNT(*) AS total,
              SUM(CASE WHEN status='ok' THEN 1 ELSE 0 END) AS ok_count,
              SUM(CASE WHEN status!='ok' THEN 1 ELSE 0 END) AS error_count
            FROM agent_episode_actions WHERE episode_id=?
            """,
            (episode_id,),
        ).fetchone()
        success = 1 if status in {"completed", "ok", "success"} else 0
        grounded = 1 if components.get("groundedness", 0) >= 0.5 else 0
        errors = int(action_stats["error_count"] or 0)
        conn.execute(
            """
            INSERT INTO agent_strategy_stats
            (owner_scope, context_key, strategy_id, sample_count, reward_sum,
             reward_sum_squares, success_count, grounded_count, error_count,
             latency_sum_ms, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(owner_scope, context_key, strategy_id) DO UPDATE SET
              sample_count=sample_count+excluded.sample_count,
              reward_sum=reward_sum+excluded.reward_sum,
              reward_sum_squares=reward_sum_squares+excluded.reward_sum_squares,
              success_count=success_count+excluded.success_count,
              grounded_count=grounded_count+excluded.grounded_count,
              error_count=error_count+excluded.error_count,
              latency_sum_ms=latency_sum_ms+excluded.latency_sum_ms,
              updated_at=excluded.updated_at
            """,
            (
                owner,
                row["context_key"],
                row["strategy_id"],
                1,
                reward,
                reward * reward,
                success,
                grounded,
                errors,
                float(latency_ms or 0),
                completed_at,
            ),
        )
        result = dict(
            conn.execute(
                "SELECT * FROM agent_episodes WHERE episode_id=?",
                (episode_id,),
            ).fetchone()
        )
    return result


def record_outcome(
    *,
    episode_id: str,
    owner_scope: str,
    success: bool,
    outcome_code: str | None = None,
    evidence_status: str | None = None,
    latency_ms: float | None = None,
    idempotency_key: str | None = None,
) -> dict:
    record_reward_event(
        episode_id=episode_id,
        owner_scope=owner_scope,
        source="task_success",
        value=1.0 if success else -1.0,
        evidence={"outcome_code": outcome_code},
        idempotency_key=idempotency_key or f"{episode_id}:outcome",
    )
    if evidence_status:
        record_reward_event(
            episode_id=episode_id,
            owner_scope=owner_scope,
            source="groundedness",
            value=1.0 if evidence_status in {"sufficient", "grounded", "valid"} else -0.5,
            evidence={"status": evidence_status},
            idempotency_key=f"{episode_id}:groundedness",
        )
    return finish_episode(
        episode_id=episode_id,
        owner_scope=owner_scope,
        status="completed" if success else "failed",
        outcome_code=outcome_code,
        latency_ms=latency_ms,
    )


def record_feedback_event(
    *,
    episode_id: str,
    owner_scope: str,
    feedback_type: str,
    feedback_text: str,
    idempotency_key: str | None = None,
) -> dict:
    value = 1.0 if feedback_type == "praise" else -1.0 if feedback_type in {"correction", "bug"} else 0.0
    return record_reward_event(
        episode_id=episode_id,
        owner_scope=owner_scope,
        source="user_feedback",
        value=value,
        evidence={"feedback_type": feedback_type, "text": feedback_text[:400]},
        idempotency_key=idempotency_key or f"{episode_id}:feedback:{hashlib.sha256(feedback_text.encode()).hexdigest()[:12]}",
    )


def strategy_rank(
    *,
    owner_scope: str,
    context: dict[str, Any] | None = None,
    limit: int = 5,
) -> dict:
    _ensure()
    owner = _owner(owner_scope)
    context_data = context or {}
    ctx = context_key(
        domain=str(context_data.get("domain", "")),
        intent=str(context_data.get("intent", "")),
        modality=str(context_data.get("modality", "text")),
        risk_class=str(context_data.get("risk_class", "read")),
        task_type=str(context_data.get("task_type", "")),
    )
    exploration = float(getattr(get_settings(), "LIGHTNING_EXPLORATION_RATE", 0.10))
    minimum = int(getattr(get_settings(), "LIGHTNING_MIN_SAMPLES_PER_STRATEGY", 20))
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM agent_strategy_stats WHERE owner_scope=? AND context_key=?",
            (owner, ctx),
        ).fetchall()
        total = sum(int(row["sample_count"]) for row in rows)
    ranked = []
    for row in rows:
        count = int(row["sample_count"])
        mean = float(row["reward_sum"]) / max(count, 1)
        bonus = math.sqrt(math.log(max(total, 1) + 1) / count) if count else 1.0
        score = mean + exploration * bonus
        ranked.append(
            {
                "strategy_id": row["strategy_id"],
                "sample_count": count,
                "mean_reward": round(mean, 6),
                "ucb_score": round(score, 6),
                "success_rate": round(int(row["success_count"]) / max(count, 1), 6),
                "grounded_rate": round(int(row["grounded_count"]) / max(count, 1), 6),
                "error_count": int(row["error_count"]),
                "latency_avg_ms": round(float(row["latency_sum_ms"]) / max(count, 1), 3),
                "exploration_required": count < minimum,
            }
        )
    ranked.sort(key=lambda item: (-item["ucb_score"], item["strategy_id"]))
    return {
        "context_key": ctx,
        "strategies": ranked[: max(1, min(limit, 50))],
        "cold_start": not bool(ranked),
        "exploration_rate": exploration,
        "minimum_samples": minimum,
    }


def reward_summary(
    *,
    owner_scope: str,
    window_days: int = 7,
    context_key_value: str | None = None,
) -> dict:
    _ensure()
    owner = _owner(owner_scope)
    since = (datetime.now(UTC) - timedelta(days=max(1, window_days))).isoformat()
    with connect() as conn:
        query = "SELECT * FROM agent_episodes WHERE owner_scope=? AND started_at>=?"
        params: list[Any] = [owner, since]
        if context_key_value:
            query += " AND context_key=?"
            params.append(context_key_value)
        rows = conn.execute(query, params).fetchall()
    episodes = [dict(row) for row in rows]
    count = len(episodes)
    rewards = [float(row["reward"]) for row in episodes if row["reward"] is not None]
    completed = sum(row["status"] in {"completed", "ok", "success"} for row in episodes)
    failed = sum(row["status"] in {"failed", "error", "timeout"} for row in episodes)
    grounded = sum(
        json.loads(row["reward_breakdown_json"] or "{}").get("components", {}).get("groundedness", 0) >= 0.5
        for row in episodes
    )
    return {
        "window_days": window_days,
        "context_key": context_key_value,
        "episodes": count,
        "reward_mean": round(sum(rewards) / len(rewards), 6) if rewards else 0.0,
        "success_rate": round(completed / max(count, 1), 6),
        "failure_rate": round(failed / max(count, 1), 6),
        "grounded_rate": round(grounded / max(count, 1), 6),
        "latency_avg_ms": round(
            sum(float(row["latency_ms"] or 0) for row in episodes) / max(count, 1),
            3,
        ),
    }


def regression_check(
    *,
    owner_scope: str,
    baseline_strategy_id: str,
    candidate_strategy_id: str,
    window_days: int = 7,
    context_key_value: str | None = None,
) -> dict:
    _ensure()
    owner = _owner(owner_scope)
    since = (datetime.now(UTC) - timedelta(days=max(1, window_days))).isoformat()

    def metrics(conn, strategy: str) -> dict:
        query = "SELECT * FROM agent_episodes WHERE owner_scope=? AND strategy_id=? AND started_at>=?"
        params: list[Any] = [owner, strategy, since]
        if context_key_value:
            query += " AND context_key=?"
            params.append(context_key_value)
        rows = conn.execute(query, params).fetchall()
        count = len(rows)
        rewards = [float(row["reward"]) for row in rows if row["reward"] is not None]
        return {
            "samples": count,
            "reward_mean": sum(rewards) / len(rewards) if rewards else 0.0,
            "success_rate": sum(row["status"] in {"completed", "ok", "success"} for row in rows) / max(count, 1),
            "error_rate": sum(row["status"] in {"failed", "error", "timeout"} for row in rows) / max(count, 1),
            "latency_avg_ms": sum(float(row["latency_ms"] or 0) for row in rows) / max(count, 1),
        }

    with connect() as conn:
        baseline = metrics(conn, baseline_strategy_id)
        candidate = metrics(conn, candidate_strategy_id)
        minimum = int(getattr(get_settings(), "LIGHTNING_MIN_SAMPLES_PER_STRATEGY", 20))
        enough = min(baseline["samples"], candidate["samples"]) >= minimum
        rollback = enough and (
            candidate["reward_mean"] <= baseline["reward_mean"] - 0.15
            or candidate["error_rate"] >= baseline["error_rate"] + 0.10
            or candidate["latency_avg_ms"] >= baseline["latency_avg_ms"] * 1.25
        )
        evaluation_id = _id("EV")
        status = "rollback_recommended" if rollback else "pass" if enough else "insufficient_data"
        conn.execute(
            """
            INSERT INTO agent_evaluations
            (evaluation_id, owner_scope, context_key, baseline_strategy_id,
             candidate_strategy_id, window_start, window_end,
             baseline_metrics_json, candidate_metrics_json, sample_count,
             status, rollback_recommended, created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                evaluation_id,
                owner,
                context_key_value,
                baseline_strategy_id,
                candidate_strategy_id,
                since,
                _now(),
                _json(baseline),
                _json(candidate),
                min(baseline["samples"], candidate["samples"]),
                status,
                int(rollback),
                _now(),
            ),
        )
    return {
        "evaluation_id": evaluation_id,
        "status": status,
        "rollback_recommended": rollback,
        "baseline": baseline,
        "candidate": candidate,
        "minimum_samples": minimum,
    }


def list_recent_errors(*, owner_scope: str, limit: int = 20) -> list[dict]:
    _ensure()
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT e.episode_id, e.strategy_id, e.context_key, e.status,
                   e.outcome_code, e.reward, e.started_at, a.action_name,
                   a.error_type
            FROM agent_episodes e
            LEFT JOIN agent_episode_actions a ON a.episode_id=e.episode_id
            WHERE e.owner_scope=? AND (e.status IN ('failed','error','timeout') OR a.status!='ok')
            ORDER BY e.id DESC LIMIT ?
            """,
            (_owner(owner_scope), max(1, min(limit, 100))),
        ).fetchall()
    return [dict(row) for row in rows]
