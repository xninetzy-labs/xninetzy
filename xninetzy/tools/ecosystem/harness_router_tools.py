from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any

from langchain_core.tools import tool

from xninetzy.db.migrations import run_migrations
from xninetzy.db.sqlite import connect
from xninetzy.tools.tool_results import to_tool_result


_INTENT_KEYWORDS = {
    "audit": ("security", {"security_scope", "security_assets", "security_sast", "security_dependencies", "security_headers", "security_threat_model", "security_validate_finding"}),
    "scanning": ("security", {"security_scope", "security_assets", "security_sast", "security_headers"}),
    "vulnerability": ("security", {"security_sast", "security_dependencies", "security_threat_model", "security_validate_finding"}),
    "penetration": ("security", {"security_scope", "security_assets", "security_headers", "security_threat_model"}),
    "exploit": ("security", {"security_threat_model", "security_validate_finding"}),
    "pentest": ("security", {"security_scope", "security_sast", "security_headers"}),
    "code": ("engineering", {"repo_search", "repo_symbol", "repo_dependency", "repo_architecture", "repo_risk"}),
    "refactor": ("engineering", {"repo_search", "repo_symbol", "repo_dependency", "repo_test", "repo_diff"}),
    "debug": ("engineering", {"repo_search", "repo_symbol", "repo_diff", "repo_test"}),
    "test": ("engineering", {"repo_test", "repo_search", "repo_symbol"}),
    "test generation": ("engineering", {"repo_test", "repo_search", "repo_symbol"}),
    "performance": ("engineering", {"repo_search", "repo_diff", "repo_risk"}),
    "memory": ("knowledge", {"memory_episode_search", "memory_relevance", "memory_promote"}),
    "learn": ("learning", {"learning_get_roadmap", "learning_list_study_sessions", "learning_get_study_progress"}),
    "research": ("research", {"research_light", "deep_research_topic", "web_search", "web_extract", "web_evidence"}),
    "find paper": ("research", {"research_search_papers", "research_get_paper"}),
    "document": ("knowledge", {"unified_search", "knowledge_search", "knowledge_answer"}),
    "image": ("vision", {"image_inspect", "image_preprocess", "image_ocr", "image_regions", "image_compare"}),
    "screenshot": ("vision", {"image_inspect", "image_preprocess", "image_ocr", "image_layout"}),
    "ocr": ("vision", {"image_ocr", "image_preprocess", "image_regions"}),
    "inbox": ("life", {"os_inbox", "os_triage", "task_capture"}),
    "task": ("life", {"task_capture", "task_list", "task_today"}),
    "goal": ("life", {"goal_create", "goal_list", "goal_review"}),
    "habit": ("life", {"habit_log", "habit_today"}),
    "money": ("life", {"money_add_transaction", "money_summary"}),
    "workout": ("life", {"workout_log", "workout_summary"}),
    "reminder": ("life", {"reminder_create", "reminder_list"}),
    "checkpoint": ("observability", {"observability_checkpoint", "observability_recent_checkpoints"}),
    "metric": ("observability", {"observability_summary", "observability_query"}),
    "improvement": ("improvement", {"improvement_propose", "improvement_list", "improvement_evaluate"}),
    "procedure": ("harness", {"harness_plan", "harness_trace", "harness_review"}),
}


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
    ranked = _score_intent(query, _INTENT_KEYWORDS)
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
        "TOOL_NOT_FOUND": {"action": "discover", "tools": ["skill_list", "skill_suggest_for_request", "unified_search"]},
        "TIMEOUT": {"action": "shrink_scope_then_retry", "tools": ["repo_search", "image_inspect", "knowledge_search"]},
        "RATE_LIMIT": {"action": "backoff_alternate_source", "tools": ["web_search", "research_search_papers"]},
        "PARSING_FAILURE": {"action": "alternate_parser", "tools": ["web_extract", "document_analyze", "image_ocr"]},
        "OCR_FAILURE": {"action": "preprocess_alt_engine", "tools": ["image_preprocess", "image_crop", "image_ocr"]},
        "VISION_FAILURE": {"action": "smaller_roi_then_retry", "tools": ["image_crop", "image_regions", "image_inspect"]},
        "WEB_EXTRACTION_FAILURE": {"action": "alternate_source", "tools": ["web_search", "research_web_collect", "web_compare"]},
        "VERIFICATION_FAILURE": {"action": "gather_more_evidence", "tools": ["repo_search", "web_extract", "knowledge_search", "memory_relevance"]},
        "BAD_HYPOTHESIS": {"action": "re_research", "tools": ["research_light", "memory_relevance"]},
        "WRONG_TOOL": {"action": "intent_resolve_then_route", "tools": ["intent_resolve", "memory_relevance"]},
        "WRONG_ORDER": {"action": "harness_plan", "tools": ["harness_plan", "harness_record_step", "harness_verify"]},
        "INSUFFICIENT_EVIDENCE": {"action": "deep_research_then_extract", "tools": ["deep_research_topic", "web_extract", "web_evidence"]},
        "SIDE_EFFECT": {"action": "rollback_then_audit", "tools": ["harness_recover", "improvement_regress"]},
        "ENVIRONMENT_FAILURE": {"action": "retry_with_different_runtime", "tools": ["action_policy_evaluate", "os_job_status"]},
        "MODEL_REASONING_FAILURE": {"action": "fallback_template", "tools": ["memory_relevance", "memory_promote"]},
        "AUTH_FAILURE": {"action": "scope_gate_revalidate", "tools": ["security_scope", "hitl_request_approval"]},
    }
    picked = strategies.get(normalized)
    if picked is None:
        picked = {"action": "classify_first", "tools": ["memory_failure_store", "memory_relevance"]}
    payload = {
        "failure_class": normalized,
        "attempted_tool": attempted_tool,
        "last_error": last_error,
        "strategy": picked["action"],
        "candidate_tools": picked["tools"],
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
