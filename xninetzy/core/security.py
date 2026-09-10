from __future__ import annotations

import re
from typing import Any


CHAT_ID_PATTERN = re.compile(
    r"(?P<local>[A-Za-z0-9][A-Za-z0-9._:\-]*)@"
    r"(?P<domain>[A-Za-z0-9][A-Za-z0-9._\-]*)\b"
)


JID_PATTERN = CHAT_ID_PATTERN  # backwards-compatible alias


def _mask_local(local: str) -> str:
    digits = "".join(ch for ch in local.split(":", 1)[0] if ch.isdigit())
    if len(digits) < 6:
        return "[redacted]"
    return f"{digits[:4]}{'*' * (len(digits) - 6)}{digits[-2:]}"


def redact_chat_ids_in_text(text: str) -> str:
    """Mask chat identifiers inside arbitrary tool output text."""
    return CHAT_ID_PATTERN.sub(
        lambda match: f"{_mask_local(match.group('local'))}@{match.group('domain')}",
        text,
    )


def redact_jids_in_text(text: str) -> str:
    """Backwards-compatible alias for redact_chat_ids_in_text."""
    return redact_chat_ids_in_text(text)


def sanitize_tool_output(value: Any) -> Any:
    """Recursively redact chat identifiers from tool output structures."""
    if isinstance(value, str):
        return redact_chat_ids_in_text(value)
    if isinstance(value, dict):
        return {key: sanitize_tool_output(item) for key, item in value.items()}
    if isinstance(value, list):
        return [sanitize_tool_output(item) for item in value]
    if isinstance(value, tuple):
        return tuple(sanitize_tool_output(item) for item in value)
    return value
