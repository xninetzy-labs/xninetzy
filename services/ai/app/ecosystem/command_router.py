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
}

# /helper <topic> → helper_get with topic
HELPER_PATTERN = re.compile(r"^/helper\s+(\w+)$", re.I)


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

    # exact match
    cmd = stripped.split()[0].lower()
    tool = SLASH_COMMANDS.get(cmd)
    if tool:
        return tool, {}

    return None, {}
