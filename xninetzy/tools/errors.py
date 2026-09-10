from __future__ import annotations

import re
from enum import Enum


class ToolErrorCode(str, Enum):
    INVALID_INPUT = "INVALID_INPUT"
    NOT_FOUND = "NOT_FOUND"
    NOT_CONFIGURED = "NOT_CONFIGURED"
    POLICY_HELD = "POLICY_HELD"
    SERVER_ERROR = "SERVER_ERROR"


ERROR_CODE_PATTERN = re.compile(
    r"\[(INVALID_INPUT|NOT_FOUND|NOT_CONFIGURED|POLICY_HELD|SERVER_ERROR)\]"
)


def tool_error(
    code: ToolErrorCode | str,
    message: str,
    *,
    valid_values: list[str] | None = None,
) -> str:
    """Format a tool failure as the stable ``<emoji> [CODE] message`` contract."""
    code_value = code.value if isinstance(code, ToolErrorCode) else str(code)
    text = f"❌ [{code_value}] {message}"
    if valid_values:
        text += " Nilai valid: " + ", ".join(valid_values) + "."
    return text


def parse_tool_error(text: str) -> tuple[str, str] | None:
    """Extract ``(code, message)`` from a contract-formatted error string."""
    match = ERROR_CODE_PATTERN.search(text)
    if not match:
        return None
    code = match.group(1)
    message = text[match.end() :].strip()
    return code, message
