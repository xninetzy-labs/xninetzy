from __future__ import annotations

import re

# Maps slash commands to (tool_name, args_dict) or special handler keys
SLASH_COMMANDS: dict[str, str] = {
    "/helper": "helper_get",
    "/today": "task_today",
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
}

WORKFLOW_RESUME_PATTERN = re.compile(r"^/workflow-resume\s+([\w-]+)$", re.I)
WORKFLOW_CANCEL_PATTERN = re.compile(r"^/workflow-cancel\s+([\w-]+)$", re.I)

# /helper <topic> → helper_get with topic
HELPER_PATTERN = re.compile(r"^/helper\s+(\w+)$", re.I)
SKILL_PATTERN = re.compile(r"^/skill\s+([\w-]+)$", re.I)
APPROVE_PATTERN = re.compile(r"^/approve\s+(\d+)$", re.I)
REJECT_PATTERN = re.compile(r"^/reject\s+(\d+)$", re.I)
RESEARCH_PATTERN = re.compile(r"^/research\s+(.+)$", re.I | re.S)
DEEP_RESEARCH_PATTERN = re.compile(r"^/deep-research(?:\s+(speed|balanced|quality))?\s+(.+)$", re.I | re.S)

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
FEEDBACK_PATTERN = re.compile(r"^/(?:feedback|fix-agent|agent-learn)\s+(.+)$", re.I | re.S)
AGENT_APPROVE_PATTERN = re.compile(r"^/agent-approve\s+(\d+)$", re.I)
AGENT_REJECT_PATTERN = re.compile(r"^/agent-reject\s+(\d+)$", re.I)


def parse_command(message: str) -> tuple[str | None, dict]:
    """
    Returns (tool_name, kwargs) if message is a slash command, else (None, {}).
    """
    stripped = message.strip()
    if not stripped.startswith("/"):
        return None, {}

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
        return "deep_research_topic", {"mode": (m.group(1) or "balanced").lower(), "topic": m.group(2).strip()}

    m = RESEARCH_PATTERN.match(stripped)
    if m:
        return "research_light", {"topic": m.group(1).strip()}

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
