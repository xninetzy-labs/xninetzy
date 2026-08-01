from __future__ import annotations

import re

# Maps slash commands to (tool_name, args_dict) or special handler keys
SLASH_COMMANDS: dict[str, str] = {
    "/helper": "helper_get",
    "/today": "os_today",
    "/inbox": "os_inbox",
    "/goals": "goal_list",
    "/tasks": "task_today",
    "/money": "money_summary",
    "/workout": "workout_summary",
    "/hebat": "hebat_academic_digest",
    "/review": "daily_review_generate",
    "/knowledge": "knowledge_search",
    "/skills": "skill_list",
    "/research": "research_light",
    "/deep-research": "deep_research_topic",
    "/roadmaps": "learning_list_roadmaps",
    "/roadmap": "learning_list_roadmaps",
    "/study-today": "learning_generate_today_plan",
    "/study-review": "learning_review_week",
    "/approvals": "hitl_list_pending",
    "/hebat-debug": "hebat_debug_login",
    "/nilai": "portal_grades",
    "/jadwal": "portal_schedule",
    "/cyber-profile": "portal_profile",
    "/status-akademik": "portal_academic_status",
    "/portalinfo": "portal_info",
    "/portal-nav": "portal_navigation",
    "/krs-capabilities": "portal_krs_capabilities",
    "/krs-watcher": "portal_krs_watcher_status",
    "/krs-war": "portal_krs_war_status",
    "/web-analysis": "web_analysis_status",
    "/web-discover": "web_discover",
    "/media-info": "media_info",
    "/analyze-media": "analyze_media",
    "/rule": "rule_list",
    "/rules": "rule_list",
    "/style": "style_show",
    "/test-rules": "rules_healthcheck",
    "/memory": "memory_list",
    "/agent-proposals": "lightning_list_proposals",
    "/agent-improve": "lightning_improve",
    "/agent-errors": "lightning_errors",
    "/test-lightning": "lightning_healthcheck",
    "/test-memory": "memory_list",
    "/workflow-status": "workflow_status",
    "/workflow-latest": "workflow_latest",
    "/llm": "ai_provider_status",
    "/agent": "coding_agent_status",
}

WORKFLOW_RESUME_PATTERN = re.compile(r"^/workflow-resume\s+([\w-]+)$", re.I)
WORKFLOW_CANCEL_PATTERN = re.compile(r"^/workflow-cancel\s+([\w-]+)$", re.I)
LLM_LIST_PATTERN = re.compile(r"^/llm\s+list$", re.I)
LLM_USE_PATTERN = re.compile(r"^/llm\s+use\s+([\w-]+)(?:\s+(.+))?$", re.I | re.S)
AGENT_LIST_PATTERN = re.compile(r"^/agent\s+list$", re.I)
AGENT_USE_PATTERN = re.compile(r"^/agent\s+use\s+([\w-]+)$", re.I)
CODE_PATTERN = re.compile(r"^/code\s+(.+)$", re.I | re.S)
CAPTURE_PATTERN = re.compile(r"^/capture\s+(.+)$", re.I | re.S)
TRIAGE_PATTERN = re.compile(r"^/triage\s+(\d+)\s+(task|archive)$", re.I)
CAPTCHA_PATTERN = re.compile(r"^/captcha\s+([A-Za-z0-9_-]+)\s+([^\s]+)$", re.I)
GRADE_TOKEN_PATTERN = re.compile(
    r"^/grade-token\s+([A-Za-z0-9_-]+)\s+(\d{4,10})$", re.I
)
GRADE_REQUEST_PATTERN = re.compile(r"^/nilai(?:\s+(.+))?$", re.I)
GRADE_CHANGES_PATTERN = re.compile(
    r"^/nilai\s+(?:changes|perubahan)(?:\s+(.+))?$",
    re.I,
)
KRS_STATUS_PATTERN = re.compile(r"^/krs\s+status$", re.I)
KRS_WAR_PATTERN = re.compile(r"^/krs-war(?:\s+(status|arm|disarm|plan|dry-run))?$", re.I)
CONCEPT_MAP_PATTERN = re.compile(r"^/concepts\s+(\d+)$", re.I)
RECALL_ANSWER_PATTERN = re.compile(
    r"^/recall\s+answer\s+(\d+)\s+([1-5])\s+(.+)$", re.I | re.S
)
RECALL_DUE_PATTERN = re.compile(r"^/recall(?:\s+(\d+))?$", re.I)
CYBER_LOGIN_CANCEL_PATTERN = re.compile(
    r"^/cyber-login-cancel\s+([A-Za-z0-9_-]+)$", re.I
)

# /helper <topic> → helper_get with topic
HELPER_PATTERN = re.compile(r"^/helper\s+(\w+)$", re.I)
SKILL_PATTERN = re.compile(r"^/skill\s+([\w-]+)$", re.I)
APPROVE_PATTERN = re.compile(r"^/approve\s+(\d+)$", re.I)
REJECT_PATTERN = re.compile(r"^/reject\s+(\d+)$", re.I)
RESEARCH_PATTERN = re.compile(r"^/research\s+(.+)$", re.I | re.S)
DEEP_RESEARCH_PATTERN = re.compile(
    r"^/deep-research(?:\s+(speed|balanced|quality))?\s+(.+)$", re.I | re.S
)
WEB_ANALYSIS_PATTERN = re.compile(r"^/web-analysis\s+(hebat|mahasiswa|qa)$", re.I)
WEB_REFRESH_PATTERN = re.compile(r"^/web-refresh\s+(hebat|mahasiswa|qa)$", re.I)
WEB_CATALOG_PATTERN = re.compile(r"^/web-pages\s+(hebat|mahasiswa|qa)$", re.I)
WEB_DISCOVER_PATTERN = re.compile(r"^/web-discover(?:\s+(\d+))?\s+(https://\S+)$", re.I)

RULE_ADD_PATTERN = re.compile(r"^/rule\s+add\s+(.+)$", re.I | re.S)
RULE_OFF_PATTERN = re.compile(r"^/rule\s+off\s+(\d+)$", re.I)
RULE_ON_PATTERN = re.compile(r"^/rule\s+on\s+(\d+)$", re.I)
RULE_DELETE_PATTERN = re.compile(r"^/rule\s+(?:delete|del|rm)\s+(\d+)$", re.I)
RULE_SEARCH_PATTERN = re.compile(r"^/rule\s+search\s+(.+)$", re.I | re.S)
RULE_LIST_PATTERN = re.compile(r"^/rule\s+list$", re.I)
STYLE_SET_PATTERN = re.compile(r"^/style\s+set\s+(.+)$", re.I | re.S)
STYLE_RESET_PATTERN = re.compile(r"^/style\s+reset$", re.I)
STYLE_SHOW_PATTERN = re.compile(r"^/style\s+show$", re.I)

REMEMBER_PATTERN = re.compile(r"^/remember\s+(.+)$", re.I | re.S)
MEMORY_SEARCH_PATTERN = re.compile(r"^/memory\s+search\s+(.+)$", re.I | re.S)
MEMORY_DELETE_PATTERN = re.compile(r"^/memory\s+(?:delete|del|rm)\s+(\d+)$", re.I)
FORGET_MEMORY_PATTERN = re.compile(r"^/forget-memory\s+(\d+)$", re.I)
FEEDBACK_PATTERN = re.compile(
    r"^/(?:feedback|fix-agent|agent-learn)\s+(.+)$", re.I | re.S
)
AGENT_APPROVE_PATTERN = re.compile(r"^/agent-approve\s+(\d+)$", re.I)
AGENT_REJECT_PATTERN = re.compile(r"^/agent-reject\s+(\d+)$", re.I)


def parse_command(message: str) -> tuple[str | None, dict]:
    """
    Returns (tool_name, kwargs) if message is a slash command, else (None, {}).
    """
    stripped = message.strip()
    if not stripped.startswith("/"):
        return None, {}

    if LLM_LIST_PATTERN.match(stripped):
        return "ai_provider_list", {}
    m = LLM_USE_PATTERN.match(stripped)
    if m:
        return "ai_provider_use", {
            "provider": m.group(1).lower(),
            "model": (m.group(2) or "").strip(),
        }

    if AGENT_LIST_PATTERN.match(stripped):
        return "coding_agent_list", {}
    m = AGENT_USE_PATTERN.match(stripped)
    if m:
        return "coding_agent_use", {"runtime": m.group(1).lower()}

    m = CODE_PATTERN.match(stripped)
    if m:
        return "coding_agent_run", {"task": m.group(1).strip()}

    m = CAPTURE_PATTERN.match(stripped)
    if m:
        return "os_capture", {"content": m.group(1).strip()}
    m = TRIAGE_PATTERN.match(stripped)
    if m:
        return "os_triage", {
            "capture_id": int(m.group(1)),
            "target": m.group(2).lower(),
        }

    if stripped.lower() == "/cyber-login":
        return "portal_login_start", {}
    if KRS_STATUS_PATTERN.match(stripped):
        return "portal_current_krs", {}
    m = CONCEPT_MAP_PATTERN.match(stripped)
    if m:
        return "learning_get_concept_map", {"roadmap_id": int(m.group(1))}
    m = RECALL_ANSWER_PATTERN.match(stripped)
    if m:
        return "learning_submit_recall_answer", {
            "card_id": int(m.group(1)),
            "confidence": int(m.group(2)),
            "answer": m.group(3).strip(),
        }
    m = RECALL_DUE_PATTERN.match(stripped)
    if m:
        return "learning_due_recall", {
            "roadmap_id": int(m.group(1)) if m.group(1) else None
        }
    m = GRADE_CHANGES_PATTERN.match(stripped)
    if m:
        return "portal_grade_changes", {
            "academic_period": (m.group(1) or "").strip()
        }
    m = GRADE_REQUEST_PATTERN.match(stripped)
    if m:
        return "portal_grades", {
            "academic_period": (m.group(1) or "latest").strip()
        }
    m = CAPTCHA_PATTERN.match(stripped)
    if m:
        return "portal_login_submit_captcha", {
            "challenge_id": m.group(1),
            "captcha_answer": m.group(2),
        }
    m = GRADE_TOKEN_PATTERN.match(stripped)
    if m:
        return "__portal_grade_token_submit", {
            "challenge_id": m.group(1),
            "token": m.group(2),
        }
    m = CYBER_LOGIN_CANCEL_PATTERN.match(stripped)
    if m:
        return "portal_login_cancel", {"challenge_id": m.group(1)}

    m = KRS_WAR_PATTERN.match(stripped)
    if m:
        sub = (m.group(1) or "status").lower()
        tool_name = {
            "arm": "portal_krs_war_arm",
            "disarm": "portal_krs_war_disarm",
            "plan": "portal_krs_war_plan",
            "dry-run": "portal_krs_war_dry_run",
            "status": "portal_krs_war_status",
        }[sub]
        return tool_name, {}

    # /helper <topic>
    m = HELPER_PATTERN.match(stripped)
    if m:
        return "helper_get", {"topic": m.group(1).lower()}

    m = SKILL_PATTERN.match(stripped)
    if m:
        return "skill_get", {"name": m.group(1).lower()}

    m = APPROVE_PATTERN.match(stripped)
    if m:
        return "hitl_approve", {"approval_id": int(m.group(1))}

    m = REJECT_PATTERN.match(stripped)
    if m:
        return "hitl_reject", {"approval_id": int(m.group(1))}

    m = WORKFLOW_RESUME_PATTERN.match(stripped)
    if m:
        return "workflow_resume", {"workflow_id": m.group(1)}

    m = WORKFLOW_CANCEL_PATTERN.match(stripped)
    if m:
        return "workflow_cancel", {"workflow_id": m.group(1)}

    m = DEEP_RESEARCH_PATTERN.match(stripped)
    if m:
        return "deep_research_topic", {
            "mode": (m.group(1) or "balanced").lower(),
            "topic": m.group(2).strip(),
        }

    m = RESEARCH_PATTERN.match(stripped)
    if m:
        return "research_light", {"topic": m.group(1).strip()}

    m = WEB_ANALYSIS_PATTERN.match(stripped)
    if m:
        return "web_analysis_status", {"site_slug": m.group(1).lower()}
    m = WEB_REFRESH_PATTERN.match(stripped)
    if m:
        site_slug = m.group(1).lower()
        return "web_analysis_refresh", {
            "site_slug": site_slug,
            "authenticated": site_slug in {"hebat", "mahasiswa", "qa"},
        }
    m = WEB_CATALOG_PATTERN.match(stripped)
    if m:
        return "web_analysis_catalog", {"site_slug": m.group(1).lower()}
    m = WEB_DISCOVER_PATTERN.match(stripped)
    if m:
        return "web_discover", {
            "source_url": m.group(2),
            "depth": int(m.group(1) or "1"),
        }

    # /rule subcommands
    m = RULE_ADD_PATTERN.match(stripped)
    if m:
        return "rule_add", {"content": m.group(1).strip()}
    m = RULE_OFF_PATTERN.match(stripped)
    if m:
        return "rule_disable", {"rule_id": int(m.group(1))}
    m = RULE_ON_PATTERN.match(stripped)
    if m:
        return "rule_enable", {"rule_id": int(m.group(1))}
    m = RULE_DELETE_PATTERN.match(stripped)
    if m:
        return "rule_delete", {"rule_id": int(m.group(1))}
    m = RULE_SEARCH_PATTERN.match(stripped)
    if m:
        return "rule_search", {"query": m.group(1).strip()}
    if RULE_LIST_PATTERN.match(stripped):
        return "rule_list", {}

    # /style subcommands
    m = STYLE_SET_PATTERN.match(stripped)
    if m:
        return "style_set", {"description": m.group(1).strip()}
    if STYLE_RESET_PATTERN.match(stripped):
        return "style_reset", {}
    if STYLE_SHOW_PATTERN.match(stripped):
        return "style_show", {}

    # memory commands
    m = REMEMBER_PATTERN.match(stripped)
    if m:
        return "memory_add", {"content": m.group(1).strip()}
    m = MEMORY_SEARCH_PATTERN.match(stripped)
    if m:
        return "memory_search", {"query": m.group(1).strip()}
    m = MEMORY_DELETE_PATTERN.match(stripped)
    if m:
        return "memory_forget", {"memory_id": int(m.group(1))}
    m = FORGET_MEMORY_PATTERN.match(stripped)
    if m:
        return "memory_forget", {"memory_id": int(m.group(1))}

    # lightning commands
    m = FEEDBACK_PATTERN.match(stripped)
    if m:
        return "lightning_feedback", {"feedback_text": m.group(1).strip()}
    m = AGENT_APPROVE_PATTERN.match(stripped)
    if m:
        return "lightning_approve", {"proposal_id": int(m.group(1))}
    m = AGENT_REJECT_PATTERN.match(stripped)
    if m:
        return "lightning_reject", {"proposal_id": int(m.group(1))}

    # exact match
    cmd = stripped.split()[0].lower()
    tool = SLASH_COMMANDS.get(cmd)
    if tool:
        return tool, {}

    return None, {}
