from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

DATASET_VERSION = "1.0.0"
DOMAIN_TOKEN_RULES: dict[str, set[str]] = {
    "learning": {"learning_", "roadmap", "recall", "mastery", "study_session"},
    "academic": {"hebat_", "portal_", "qa_", "uacc_", "academic_"},
    "research": {"research_", "deep_research_", "web_", "youtube_", "arxiv", "pubmed"},
    "knowledge": {"knowledge_", "memory_", "document_", "unified_", "graph_"},
    "career": {"career_"},
    "software": {"repo_", "harness_"},
    "data": {"data_", "dashboard_"},
    "security": {"security_"},
    "browser": {"playwright_", "browser_", "web_discover", "web_fetch", "web_extract"},
    "files": {"document_", "adr_generate", "implementation_record", "security_finding_record"},
    "os": {"os_", "task_", "goal_", "habit_", "money_", "workout_", "reminder_"},
    "automation": {"harness_", "workflow_"},
    "media": {"video_", "media_"},
}


_PII_PATTERNS = [
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    re.compile(r"\b\d{3}[-.\s]?\d{3,4}[-.\s]?\d{4}\b"),
    re.compile(r"(?i)(api[_-]?key|token|password|secret|cookie)\s*[:=]\s*\S+"),
]


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def bucket_domains(tool_names: list[str]) -> list[str]:
    out: set[str] = set()
    for name in tool_names:
        for domain, prefixes in DOMAIN_TOKEN_RULES.items():
            if any(p in name for p in prefixes):
                out.add(domain)
    return sorted(out)


def redact_pii(text: str) -> str:
    if not text:
        return ""
    out = text[:4000]
    for pat in _PII_PATTERNS:
        out = pat.sub("[redacted]", out)
    return out


def split_temporal(
    *,
    cutoff_test: timedelta = timedelta(days=14),
    cutoff_train_window: timedelta = timedelta(days=180),
) -> tuple[str, str, str]:
    now = datetime.now(UTC)
    test_cutoff = now - cutoff_test
    train_end = test_cutoff - timedelta(seconds=1)
    train_start = now - cutoff_train_window - cutoff_test
    return (
        train_start.isoformat(),
        train_end.isoformat(),
        (test_cutoff + timedelta(days=1)).isoformat(),
    )


def _row_to_sample(*, episode: dict[str, Any], actions: list[dict[str, Any]]) -> dict[str, Any] | None:
    tools_used = [str(a["action_name"]) for a in actions if a.get("action_name")]
    if not tools_used:
        return None
    domains = bucket_domains(tools_used)
    if not domains:
        return None
    skill_ids_raw = episode.get("skill_ids_json") or "[]"
    try:
        skills = json.loads(skill_ids_raw)
    except Exception:
        skills = []
    if not isinstance(skills, list):
        skills = []
    state_json_raw = episode.get("state_json") or "{}"
    try:
        state = json.loads(state_json_raw)
    except Exception:
        state = {}
    intent = str(episode.get("task_type") or "general")
    reward = float(episode.get("reward") or 0.0)
    outcome = str(episode.get("outcome_code") or episode.get("status") or "unknown")
    return {
        "id": f"rt-{(episode.get('episode_id') or 'unknown')[:32]}",
        "version": DATASET_VERSION,
        "split": "train",
        "input": {
            "text": redact_pii(f"task_type={intent}; tools_used={tools_used[:6]}"),
            "language": "en",
            "language_mode": "structured",
            "entities": list(tools_used[:8]),
            "constraints": [],
            "desired_output": "tool-call",
        },
        "context": {
            "chat_id": "<hashed>",
            "trace_id": episode.get("trace_id"),
            "episode_id": episode.get("episode_id"),
            "interface": episode.get("interface") or "internal",
            "turn_index": 0,
            "previous_routes": [],
        },
        "state": state if isinstance(state, dict) else {},
        "task_family": "execute",
        "expected": {
            "domains": domains,
            "skills": [str(s) for s in skills if s],
            "task": intent,
            "capabilities": sorted(set(domains)),
            "tools": list(dict.fromkeys(tools_used)),
            "providers": [],
            "risk_class": "read" if reward >= 0 else "draft",
            "fallback_tools": [],
            "explanation": "auto-bucketed from agent_episodes.actions",
        },
        "acceptable_alternatives": {"domains": [], "tools": []},
        "risk": "low",
        "difficulty": "easy",
        "expected_layer": "L6",
        "source": {
            "kind": "real-trace",
            "trace_id": episode.get("trace_id"),
            "episode_id": episode.get("episode_id"),
            "extracted_at": _utcnow(),
            "extractor": "routing_dataset_builder@1.0.0",
            "privacy_pass": "pii_filter",
            "human_validated": False,
        },
        "outcome_code": outcome,
    }


def build_dataset(*, source: str = "agent_episodes", max_rows: int | None = None) -> list[dict[str, Any]]:
    from xninetzy.db.sqlite import connect, init_db
    from xninetzy.db.migrations import run_migrations

    init_db()
    run_migrations()
    out: list[dict[str, Any]] = []
    with connect() as conn:
        eps = conn.execute(
            "SELECT episode_id, owner_scope, interface, chat_id, message_id, trace_id, "
            "context_key, strategy_id, task_type, status, outcome_code, started_at, "
            "completed_at, reward, skill_ids_json, state_json FROM agent_episodes "
            "WHERE completed_at IS NOT NULL ORDER BY started_at DESC"
        ).fetchall()
        for ep_row in eps:
            ep = dict(ep_row)
            actions = conn.execute(
                "SELECT action_name, action_type, status FROM agent_episode_actions "
                "WHERE episode_id=? ORDER BY ordinal",
                (ep["episode_id"],),
            ).fetchall()
            sample = _row_to_sample(episode=ep, actions=[dict(a) for a in actions])
            if sample is not None:
                out.append(sample)
            if max_rows is not None and len(out) >= max_rows:
                break
    return out


def split_dataset(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    train_start, train_end, test_start = split_temporal()
    train_holder: list[dict[str, Any]] = []
    val_holder: list[dict[str, Any]] = []
    test_holder: list[dict[str, Any]] = []
    train_start_dt = datetime.fromisoformat(train_start)
    train_end_dt = datetime.fromisoformat(train_end)
    for row in rows:
        started_at = str(row.get("context", {}).get("episode_id") or "")
        now = datetime.now(UTC)
        if started_at == "rt-auto":
            now = now
        if train_start_dt <= now <= train_end_dt:
            train_holder.append(row)
        elif now < train_start_dt:
            val_holder.append(row)
        else:
            test_holder.append(row)
    if not train_holder and rows:
        bucket = max(1, int(len(rows) * 0.7))
        val_bucket = max(1, int(len(rows) * 0.15))
        train_holder = rows[:bucket]
        val_holder = rows[bucket : bucket + val_bucket]
        test_holder = rows[bucket + val_bucket :]
    return {"train": train_holder, "val": val_holder, "test": test_holder}


def adversarial_curated_set() -> list[dict[str, Any]]:
    samples: list[dict[str, Any]] = []

    def _row(text: str, domains: list[str], tools: list[str], task: str, *, risk: str = "read", difficulty: str = "medium") -> dict[str, Any]:
        sid_seed = f"{text}|{'-'.join(domains)}"
        return {
            "id": "rt-curated-" + hashlib.sha256(sid_seed.encode("utf-8")).hexdigest()[:16],
            "version": DATASET_VERSION,
            "split": "adversarial",
            "input": {
                "text": redact_pii(text),
                "language": "en",
                "language_mode": "natural",
                "entities": tools,
                "constraints": [],
                "desired_output": "tool-call",
            },
            "context": {"chat_id": "<hashed>", "interface": "internal", "turn_index": 0},
            "state": {},
            "task_family": "execute",
            "expected": {
                "domains": domains,
                "skills": [],
                "task": task,
                "capabilities": domains,
                "tools": tools,
                "providers": [],
                "risk_class": risk,
                "fallback_tools": [],
                "explanation": "hand-curated",
            },
            "acceptable_alternatives": {"domains": [], "tools": []},
            "risk": "low",
            "difficulty": difficulty,
            "expected_layer": "L6",
            "source": {
                "kind": "hand-curated",
                "extracted_at": _utcnow(),
                "extractor": "manual",
                "privacy_pass": "pii_filter",
                "human_validated": True,
            },
        }

    pairs = [
        ("find papers on adaptive learning", ["research"], ["research_search_papers"], "literature.search"),
        ("research papers", ["research"], ["research_search_papers"], "literature.search"),
        ("find React tutorials", ["research"], ["research_search_papers"], "literature.search"),
        ("find React internships", ["career"], ["career_search_internships"], "internship.discovery"),
        ("find remote React jobs", ["career"], ["career_search_jobs"], "job.discovery"),
        ("find remote internships", ["career"], ["career_search_internships"], "internship.discovery"),
        ("summarize my notes", ["knowledge"], ["unified_search"], "knowledge.retrieve"),
        ("summarize my research notes", ["research", "knowledge"], ["unified_search", "research_search"], "literature.search"),
        ("make a video", ["media"], ["video_project_create"], "media.plan"),
        ("render the video", ["media"], ["video_render"], "media.render"),
        ("audit my code for security", ["security", "software"], ["security_sast", "repo_search"], "security.scan"),
        ("audit my code", ["security", "software"], ["security_sast", "repo_search"], "security.scan"),
        ("audit my api for vulnerabilities", ["security"], ["security_api_inventory", "security_headers"], "security.api"),
        ("show my tasks", ["os"], ["task_list", "task_today"], "os.tasks"),
        ("today's tasks", ["os"], ["task_today"], "os.tasks"),
        ("check Moodle assignment", ["academic"], ["hebat_get_assignment_detail"], "academic.assignment"),
        ("submit to HEBAT", ["academic"], ["hebat_upload_submission"], "academic.submit"),
        ("search research papers", ["research"], ["research_search_papers"], "literature.search"),
        ("do my math homework", ["learning", "academic"], ["learning_generate_today_plan"], "learning.study"),
        ("remember this fact", ["knowledge", "memory"], ["memory_add"], "memory.write"),
        ("what do you know about", ["knowledge", "memory"], ["memory_relevance"], "memory.read"),
        ("generate dashboard", ["data"], ["dashboard_generate"], "data.dashboard"),
        ("publish my workbook", ["data"], ["tableau_publish_workbook"], "data.publish"),
        ("make dataset", ["data", "research"], ["data_generate_xlsx"], "data.artifact"),
        ("find academics near me", ["career"], ["career_search_companies"], "career.company"),
        ("write a CV", ["career"], ["career_resume_analysis"], "career.cv"),
        ("interview prep", ["career"], ["career_interview_prep"], "career.interview"),
    ]
    for text, domains, tools, task in pairs:
        samples.append(_row(text, domains, tools, task))

    multi_domain_followup = [
        ("find papers on adaptive learning", ["research"], ["research_search_papers"], "literature.search"),
        ("summarize them", ["research", "knowledge"], ["research_get_paper", "knowledge_search"], "literature.synthesize"),
        ("make slides", ["research", "media"], ["pptx_create"], "media.slides"),
        ("make a video from the slides", ["research", "media"], ["video_project_create"], "media.video"),
    ]
    for text, domains, tools, task in multi_domain_followup:
        samples.append(_row(text, domains, tools, task, difficulty="hard"))

    negation_pairs = [
        ("include only academic sources", ["research"], ["research_search_papers"], "literature.search"),
        ("exclude academic sources", ["research"], ["research_search"], "literature.search"),
        ("don't include academic sources", ["research"], ["research_search"], "literature.search"),
        ("without remote jobs", ["career"], ["career_search_jobs"], "job.discovery"),
        ("with resume only", ["career"], ["career_resume_analysis"], "career.cv"),
    ]
    for text, domains, tools, task in negation_pairs:
        samples.append(_row(text, domains, tools, task, difficulty="hard"))

    state_dependent = [
        ("render it", ["media"], ["video_render"], "media.render"),
        ("render it", ["media"], ["video_project_create"], "media.plan"),
    ]
    samples.append(_row("render it", state_dependent[0][1], state_dependent[0][2], state_dependent[0][3], difficulty="hard"))
    samples.append(_row("render it", state_dependent[1][1], state_dependent[1][2], state_dependent[1][3], difficulty="hard"))
    return samples


def write_dataset(output_root: str | Path = "data/routing_dataset", *, max_rows: int | None = None) -> dict[str, Any]:
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    raw = build_dataset(max_rows=max_rows)
    splits = split_dataset(raw)
    adversarial = adversarial_curated_set()
    raw_path = root / "raw.jsonl"
    _write_jsonl(raw_path, raw)
    paths: dict[str, Path] = {"raw": raw_path}
    for name, rows in splits.items():
        p = root / f"{name}.jsonl"
        _write_jsonl(p, rows)
        paths[name] = p
    adv_path = root / "adversarial_curated.jsonl"
    _write_jsonl(adv_path, adversarial)
    paths["adversarial_curated"] = adv_path
    coverage_path = root / "coverage_report.md"
    coverage_path.write_text(_render_coverage(splits, adversarial, paths), encoding="utf-8")
    paths["coverage"] = coverage_path
    return {
        "raw": raw,
        "splits": splits,
        "adversarial_curated": adversarial,
        "paths": {k: str(v) for k, v in paths.items()},
    }


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(r, ensure_ascii=False, sort_keys=True) for r in rows]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def _render_coverage(splits: dict[str, list[dict[str, Any]]], adversarial: list[dict[str, Any]], paths: dict[str, Path]) -> str:
    lines: list[str] = ["# Routing dataset coverage", ""]
    lines.append(f"Generated: `{datetime.now(UTC).isoformat()}`")
    lines.append("")
    lines.append("| split | rows | tools | domains |")
    lines.append("| --- | --- | --- | --- |")
    for name, rows in splits.items():
        tools = sum(len(r.get("expected", {}).get("tools", []) or []) for r in rows)
        domains = sum(len(r.get("expected", {}).get("domains", []) or []) for r in rows)
        lines.append(f"| {name} | {len(rows)} | {tools} | {domains} |")
    lines.append(f"| adversarial_curated | {len(adversarial)} | {sum(len(r.get('expected', {}).get('tools', []) or []) for r in adversarial)} | {sum(len(r.get('expected', {}).get('domains', []) or []) for r in adversarial)} |")
    lines.append("")
    domain_to_rows: dict[str, int] = {}
    for rows in [adversarial] + [s for s in splits.values()]:
        for r in rows:
            for d in r.get("expected", {}).get("domains", []) or []:
                domain_to_rows[d] = domain_to_rows.get(d, 0) + 1
    lines.append("## Domain coverage")
    lines.append("")
    for d in sorted(domain_to_rows):
        lines.append(f"- {d}: {domain_to_rows[d]} rows")
    lines.append("")
    lines.append("## Paths")
    lines.append("")
    for k, v in paths.items():
        lines.append(f"- `{k}`: `{v}`")
    return "\n".join(lines)
