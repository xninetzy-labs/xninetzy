from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any

from langchain_core.tools import tool

from xninetzy.db.migrations import run_migrations
from xninetzy.db.sqlite import connect
from xninetzy.tools.ecosystem.intent_registry import get as _intent_registry_get
from xninetzy.tools.tool_results import to_tool_result


def _get_intent_keywords() -> dict[str, tuple[str, set[str]]]:
    return _intent_registry_get()


def _bandit_scores_for(tool_names: list[str], intent_key: str) -> dict[str, float]:
    """Single-source bandit lookup. Returns {tool_name: score} for matching strategy_id='mcp:<tool>'."""
    out: dict[str, float] = {}
    if not tool_names:
        return out
    wanted = set(tool_names)
    try:
        from xninetzy.os.lightning.rl import context_key
        from xninetzy.db.sqlite import connect

        ctx = context_key(
            domain="mcp", intent=intent_key[:120], modality="text",
            risk_class="read", task_type="routing",
        )
        with connect() as conn:
            rows = conn.execute(
                "SELECT strategy_id, sample_count, reward_sum, success_count "
                "FROM agent_strategy_stats WHERE context_key=?",
                (ctx,),
            ).fetchall()
        for row in rows:
            sid = str(row["strategy_id"])
            if not sid.startswith("mcp:"):
                continue
            tname = sid[4:]
            if tname not in wanted:
                continue
            cnt = int(row["sample_count"])
            if cnt <= 0:
                continue
            mean = float(row["reward_sum"]) / cnt
            success_rate = int(row["success_count"]) / cnt
            out[tname] = round(0.6 * mean + 0.4 * success_rate, 4)
    except Exception:
        pass
    return out


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_db() -> None:
    run_migrations()


def _row_dict(row: Any) -> dict[str, Any]:
    return {key: row[key] for key in row.keys()}


def _score_intent(query: str, intent_keywords: dict[str, tuple[str, set[str]]]) -> list[tuple[str, float, set[str]]]:
    normalized = query.strip().lower()
    scores: dict[str, list[tuple[float, set[str]]]] = {}
    for keyword, (domain, members) in intent_keywords.items():
        if keyword in normalized:
            scores.setdefault(domain, []).append((1.0 / (1.0 + normalized.index(keyword) * 0.01), members))
    domain_totals: list[tuple[str, float, set[str]]] = []
    for domain, contributions in scores.items():
        total = sum(score for score, _ in contributions)
        merged = set().union(*(members for _, members in contributions))
        domain_totals.append((domain, round(total, 4), merged))
    domain_totals.sort(key=lambda item: item[1], reverse=True)
    return domain_totals


@tool
def intent_resolve(
    query: str,
    top_n: int = 3,
    chat_id: str = "system",
    sender_id: str = "",
) -> str:
    """Klasifikasikan intent + pilih kandidat tools otomatis.

    Args:
        query: Pertanyaan/task user.
        top_n: Maks domain dikembalikan (cap 5).
        chat_id: Chat ID.
        sender_id: Owner principal.
    """
    bounded_top = max(1, min(top_n, 5))
    ranked = _score_intent(query, _get_intent_keywords())
    items = [
        {
            "domain": domain,
            "score": score,
            "candidate_tools": sorted(members),
        }
        for domain, score, members in ranked[:bounded_top]
    ]
    if not items:
        items = [
            {
                "domain": "general",
                "score": 0.0,
                "candidate_tools": [
                    "unified_search",
                    "knowledge_search",
                    "memory_relevance",
                ],
            }
        ]
    return json.dumps({
        "query": query,
        "intents": items,
        "owner": sender_id,
    }, ensure_ascii=False)


def _score_tools(query: str, available: list[str], scopes: dict[str, list[str]]) -> list[dict[str, Any]]:
    normalized = query.lower()
    tokens = re.findall(r"[a-z_]+", normalized)
    scored: list[dict[str, Any]] = []
    for tool_name in available:
        name_norm = tool_name.lower().replace("_", " ")
        name_tokens = tool_name.lower().split("_")
        name_score = 0.0
        for tk in tokens:
            if tk in name_tokens or tk in name_norm:
                name_score += 0.4
            elif len(tk) >= 5 and any(tk in alias for alias in scopes.get(tool_name, [])):
                name_score += 0.2
        if not name_score:
            continue
        scored.append({
            "tool_name": tool_name,
            "score": round(name_score, 3),
            "aliases": scopes.get(tool_name, []),
        })
    if scored:
        bandit = _bandit_scores_for([s["tool_name"] for s in scored], normalized)
        if bandit:
            for item in scored:
                b = bandit.get(item["tool_name"])
                if b is None:
                    continue
                item["bandit_score"] = b
                item["score"] = round(item["score"] + 0.5 * b, 4)
    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored


@tool
def evidence_normalize(
    tool_name: str,
    evidence: list[dict[str, Any]] | None = None,
    claim: str = "",
    chat_id: str = "system",
    sender_id: str = "",
) -> str:
    """Normalisasi bukti dari satu tool jadi Claim-Evidence record.

    Args:
        tool_name: Nama tool sumber.
        evidence: Daftar evidence items (text|location|confidence|...).
        claim: Klaim utama.
        chat_id: Chat ID.
        sender_id: Owner principal.
    """
    items = evidence or []
    bounded = items[:64]
    weights = []
    for item in bounded:
        confidence = float(item.get("confidence", 0.5) or 0.0)
        weights.append(max(0.0, min(confidence, 1.0)))
    combined = round(sum(weights) / max(len(weights), 1), 4) if weights else 0.0
    return json.dumps({
        "tool_name": tool_name,
        "claim": claim,
        "evidence_items": bounded,
        "evidence_count": len(bounded),
        "combined_confidence": combined,
    }, ensure_ascii=False)


@tool
def recovery_choose(
    failure_class: str,
    attempted_tool: str = "",
    last_error: str = "",
    chat_id: str = "system",
    sender_id: str = "",
) -> str:
    """Pilih strategi recovery berdasarkan failure class.

    Args:
        failure_class: TOOL_NOT_FOUND|TIMEOUT|RATE_LIMIT|PARSING_FAILURE|...
        attempted_tool: Tool yang gagal.
        last_error: Pesan error ringkas.
        chat_id: Chat ID.
        sender_id: Owner principal.
    """
    normalized = failure_class.strip().upper()
    strategies: dict[str, dict[str, Any]] = {
        "TOOL_NOT_FOUND": {
            "action": "discover",
            "steps": [
                {"tool": "skill_list", "args": {"scope": "all"}, "output_key": "skills"},
                {"tool": "skill_suggest_for_request", "args": {"request": "{last_error}"}, "depends_on": ["skills"], "output_key": "suggested"},
                {"tool": "unified_search", "args": {"query": "{attempted_tool}"}, "output_key": "candidates"},
            ],
        },
        "TIMEOUT": {
            "action": "shrink_scope_then_retry",
            "steps": [
                {"tool": "repo_search", "args": {"query": "{attempted_tool}", "limit": 5}, "output_key": "matches"},
                {"tool": "image_inspect", "args": {"url": "{attempted_tool}"}, "optional": True, "output_key": "preview"},
            ],
        },
        "RATE_LIMIT": {
            "action": "backoff_alternate_source",
            "steps": [
                {"tool": "web_search", "args": {"query": "{attempted_tool}", "max_results": 3}, "output_key": "fallback_results"},
            ],
        },
        "PARSING_FAILURE": {
            "action": "alternate_parser",
            "steps": [
                {"tool": "web_extract", "args": {"url": "{attempted_tool}"}, "output_key": "extracted"},
                {"tool": "document_analyze", "args": {"path": "{attempted_tool}"}, "optional": True, "output_key": "doc"},
                {"tool": "image_ocr", "args": {"path": "{attempted_tool}"}, "optional": True, "output_key": "ocr"},
            ],
        },
        "OCR_FAILURE": {
            "action": "preprocess_alt_engine",
            "steps": [
                {"tool": "image_preprocess", "args": {"path": "{attempted_tool}", "mode": "high_contrast"}, "output_key": "preprocessed"},
                {"tool": "image_ocr", "args": {"path": "{preprocessed.path}"}, "depends_on": ["preprocessed"], "output_key": "ocr_v2"},
            ],
        },
        "VISION_FAILURE": {
            "action": "smaller_roi_then_retry",
            "steps": [
                {"tool": "image_inspect", "args": {"url": "{attempted_tool}"}, "output_key": "regions"},
                {"tool": "image_crop", "args": {"path": "{attempted_tool}", "region": "{regions[0].bbox}"}, "depends_on": ["regions"], "output_key": "roi"},
            ],
        },
        "WEB_EXTRACTION_FAILURE": {
            "action": "alternate_source",
            "steps": [
                {"tool": "web_search", "args": {"query": "{attempted_tool}", "max_results": 5}, "output_key": "web_alt"},
                {"tool": "research_web_collect", "args": {"query": "{attempted_tool}"}, "optional": True, "output_key": "research_alt"},
            ],
        },
        "VERIFICATION_FAILURE": {
            "action": "gather_more_evidence",
            "steps": [
                {"tool": "repo_search", "args": {"query": "{attempted_tool}"}, "output_key": "code_evidence"},
                {"tool": "web_extract", "args": {"url": "{attempted_tool}"}, "optional": True, "output_key": "web_evidence"},
                {"tool": "memory_relevance", "args": {"claim": "{last_error}"}, "output_key": "memory_evidence"},
            ],
        },
        "BAD_HYPOTHESIS": {
            "action": "re_research",
            "steps": [
                {"tool": "memory_relevance", "args": {"claim": "{attempted_tool}"}, "output_key": "past_lessons"},
                {"tool": "research_light", "args": {"query": "{attempted_tool}"}, "output_key": "fresh_research"},
            ],
        },
        "WRONG_TOOL": {
            "action": "intent_resolve_then_route",
            "steps": [
                {"tool": "intent_resolve", "args": {"query": "{attempted_tool}"}, "output_key": "resolution"},
                {"tool": "memory_relevance", "args": {"claim": "{attempted_tool}"}, "optional": True, "output_key": "memory_hint"},
            ],
        },
        "WRONG_ORDER": {
            "action": "harness_plan",
            "steps": [
                {"tool": "harness_plan", "args": {"title": "recovery:{attempted_tool}", "steps": ["resolve", "verify"]}, "output_key": "plan"},
                {"tool": "harness_execute", "args": {"plan_id": "{plan.plan_id}"}, "depends_on": ["plan"], "output_key": "exec"},
                {"tool": "harness_verify", "args": {"plan_id": "{plan.plan_id}"}, "depends_on": ["plan"], "output_key": "verified"},
            ],
        },
        "INSUFFICIENT_EVIDENCE": {
            "action": "deep_research_then_extract",
            "steps": [
                {"tool": "deep_research_topic", "args": {"query": "{attempted_tool}"}, "output_key": "research"},
                {"tool": "web_extract", "args": {"url": "{research.sources[0].url}"}, "depends_on": ["research"], "output_key": "primary"},
                {"tool": "web_evidence", "args": {"url": "{research.sources[1].url}"}, "depends_on": ["research"], "optional": True, "output_key": "secondary"},
            ],
        },
        "SIDE_EFFECT": {
            "action": "rollback_then_audit",
            "steps": [
                {"tool": "harness_recover", "args": {"plan_id": "{attempted_tool}", "strategy": "rollback"}, "output_key": "rolled_back"},
                {"tool": "improvement_regress", "args": {"proposal_id": "{attempted_tool}"}, "optional": True, "output_key": "audit"},
            ],
        },
        "ENVIRONMENT_FAILURE": {
            "action": "retry_with_different_runtime",
            "steps": [
                {"tool": "action_policy_evaluate", "args": {"tool_name": "{attempted_tool}"}, "output_key": "policy"},
            ],
        },
        "MODEL_REASONING_FAILURE": {
            "action": "fallback_template",
            "steps": [
                {"tool": "memory_relevance", "args": {"claim": "{attempted_tool}"}, "output_key": "hint"},
                {"tool": "memory_promote", "args": {"memory_id": "{hint.id}"}, "depends_on": ["hint"], "optional": True, "output_key": "promoted"},
            ],
        },
        "AUTH_FAILURE": {
            "action": "scope_gate_revalidate",
            "steps": [
                {"tool": "security_scope", "args": {"action": "{attempted_tool}"}, "output_key": "scope"},
                {"tool": "hitl_request_approval", "args": {"action": "{attempted_tool}", "reason": "{last_error}"}, "depends_on": ["scope"], "optional": True, "output_key": "approval"},
            ],
        },
    }
    picked = strategies.get(normalized)
    if picked is None:
        picked = {
            "action": "classify_first",
            "steps": [
                {"tool": "memory_failure_store", "args": {"failure_class": "{failure_class}", "title": "{attempted_tool}", "context": "{last_error}"}, "output_key": "logged"},
                {"tool": "memory_relevance", "args": {"claim": "{attempted_tool}"}, "output_key": "similar"},
            ],
        }
    steps = picked["steps"]
    for step in steps:
        try:
            from xninetzy.tools.manifest import manifest_for
            step["risk"] = manifest_for(step["tool"]).risk.value
        except Exception:
            step["risk"] = "read"
    payload = {
        "failure_class": normalized,
        "attempted_tool": attempted_tool,
        "last_error": last_error,
        "strategy": picked["action"],
        "steps": steps,
        "executable": True,
        "step_count": len(steps),
    }
    _ensure_db()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO observability_events
              (event_kind, severity, source, subject, payload_json, occurred_at)
            VALUES ('recovery_chosen', 'info', 'recovery_choose', ?, ?, ?)
            """,
            (
                f"{normalized}:{attempted_tool}",
                json.dumps(payload, ensure_ascii=False),
                _now_iso(),
            ),
        )
    return json.dumps(payload, ensure_ascii=False)


@tool
def claim_ledger_record(
    claim: str,
    source_urls: list[str],
    confidence: float,
    evidence_kind: str = "web",
    notes: str = "",
    chat_id: str = "system",
    sender_id: str = "",
    idempotency_key: str = "",
) -> str:
    """Catat klaim + sumber ke ledger persisten untuk audit nanti.

    Args:
        claim: Klaim.
        source_urls: URL sumber bukti.
        confidence: 0-1.
        evidence_kind: web|repo|doc|image|user.
        notes: Catatan.
        chat_id: Chat ID.
        sender_id: Owner principal.
        idempotency_key: Kunci opsional.
    """
    bounded_conf = max(0.0, min(confidence, 1.0))
    claim_id = f"claim-{uuid.uuid4().hex[:16]}"
    now = _now_iso()
    _ensure_db()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO observability_events
              (event_kind, severity, source, subject, payload_json, occurred_at)
            VALUES ('claim_recorded', 'info', 'claim_ledger_record', ?, ?, ?)
            """,
            (
                claim_id,
                json.dumps({
                    "claim": claim,
                    "source_urls": source_urls,
                    "evidence_kind": evidence_kind,
                    "notes": notes,
                    "owner": sender_id,
                }, ensure_ascii=False),
                now,
            ),
        )
        if bounded_conf >= 0.7:
            conn.execute(
                """
                INSERT INTO memory_episodes
                  (episode_id, scope, owner, task, intent, plan_json, actions_json,
                   outcome, verification, reward, usefulness, related_tools_json,
                   metadata_json, created_at, updated_at)
                VALUES (?, 'personal', ?, 'claim.record', ?, '[]', '[]', 'recorded',
                        ?, ?, ?, '["claim_ledger_record"]', ?, ?, ?)
                """,
                (
                    claim_id, sender_id, claim,
                    json.dumps(source_urls),
                    bounded_conf, bounded_conf,
                    json.dumps({"confidence": bounded_conf, "evidence_kind": evidence_kind, "notes": notes}),
                    now, now,
                ),
            )
    return json.dumps({
        "claim_id": claim_id,
        "claim": claim,
        "source_urls": source_urls,
        "confidence": bounded_conf,
    }, ensure_ascii=False)


@tool
def confidence_score(
    claims: list[dict[str, Any]],
    chat_id: str = "system",
    sender_id: str = "",
) -> str:
    """Hitung skor keyakinan agregat untuk sekumpulan claim.

    Args:
        claims: Daftar claim dengan field confidence + source_count.
        chat_id: Chat ID.
        sender_id: Owner principal.
    """
    if not claims:
        return json.dumps({"error": "claims kosong"}, ensure_ascii=False)
    scored = []
    for item in claims[:64]:
        conf = max(0.0, min(float(item.get("confidence", 0.0) or 0.0), 1.0))
        sources = max(0, int(item.get("source_count", 0) or 0))
        diversity_bonus = min(sources * 0.05, 0.2)
        score = round(min(1.0, conf + diversity_bonus), 4)
        scored.append({
            "claim": item.get("claim", "")[:240],
            "confidence": conf,
            "source_count": sources,
            "score": score,
        })
    scored.sort(key=lambda item: item["score"], reverse=True)
    aggregate = round(sum(c["score"] for c in scored) / len(scored), 4)
    return json.dumps({
        "claim_count": len(scored),
        "aggregate_score": aggregate,
        "scored_claims": scored,
    }, ensure_ascii=False)


@tool
def tool_route(
    query: str,
    candidate_tools: list[str] | None = None,
    top_n: int = 5,
    chat_id: str = "system",
    sender_id: str = "",
) -> str:
    """Peringkat tool_names dari query berdasarkan token match + aliases.

    Args:
        query: Pertanyaan/task.
        candidate_tools: Daftar tool dikandidat (kosong=all registered).
        top_n: Maks hasil (cap 25).
        chat_id: Chat ID.
        sender_id: Owner principal.
    """
    bounded_top = max(1, min(top_n, 50))
    from xninetzy.tools.registry import get_all_tools
    if not candidate_tools:
        candidate_tools = [tool.name for tool in get_all_tools()]
    alias_map: dict[str, list[str]] = {}
    for name in candidate_tools:
        normalized = name.lower()
        parts = normalized.split("_")
        alias_map[name] = [normalized, " ".join(parts), normalized.replace("_", "")]
    ranked = _score_tools(query, candidate_tools, alias_map)
    return to_tool_result(
        f"{len(ranked[:bounded_top])} tool cocok untuk query.",
        ranked[:bounded_top],
        query=query,
        limit=bounded_top,
    )


@tool
def task_state_record(
    intent: str,
    context: str,
    constraints: list[str] | None = None,
    required_evidence: list[str] | None = None,
    hypothesis: str = "",
    owner: str = "system",
    chat_id: str = "system",
    sender_id: str = "",
) -> str:
    """Catat task state INTENT→HYPOTHESIS untuk orkestrasi multi-turn.

    Args:
        intent: Intent utama.
        context: Konteks ringkas.
        constraints: Daftar batasan.
        required_evidence: Daftar bukti yang dibutuhkan.
        hypothesis: Hipotesis kerja.
        owner: Owner principal.
        chat_id: Chat ID.
        sender_id: Owner principal.
    """
    if not intent.strip():
        return json.dumps({"error": "intent wajib diisi"}, ensure_ascii=False)
    task_id = f"task-{uuid.uuid4().hex[:16]}"
    now = _now_iso()
    _ensure_db()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO observability_events
              (event_kind, severity, source, subject, payload_json, occurred_at)
            VALUES ('task_state', 'info', 'task_state_record', ?, ?, ?)
            """,
            (
                task_id,
                json.dumps({
                    "intent": intent,
                    "context": context,
                    "constraints": constraints or [],
                    "required_evidence": required_evidence or [],
                    "hypothesis": hypothesis,
                    "owner": owner,
                }, ensure_ascii=False),
                now,
            ),
        )
    return json.dumps({
        "task_id": task_id,
        "state": "INTENT",
        "next": "CONTEXT_GATHERING",
    }, ensure_ascii=False)
