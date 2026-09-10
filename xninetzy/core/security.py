from __future__ import annotations

import re
from typing import Any


JID_PATTERN = re.compile(
    r"(?P<local>[A-Za-z0-9][A-Za-z0-9._:\-]*)@"
    r"(?P<domain>s\.whatsapp\.net|whatsapp\.net|g\.us|broadcast)\b"
)


def _mask_local(local: str) -> str:
    digits = "".join(ch for ch in local.split(":", 1)[0] if ch.isdigit())
    if len(digits) < 6:
        return "[redacted]"
    return f"{digits[:4]}{'*' * (len(digits) - 6)}{digits[-2:]}"


def redact_jids_in_text(text: str) -> str:
    """Mask WhatsApp JIDs inside arbitrary tool output text."""
    return JID_PATTERN.sub(
        lambda match: f"{_mask_local(match.group('local'))}@{match.group('domain')}",
        text,
    )


def sanitize_tool_output(value: Any) -> Any:
    """Recursively redact WhatsApp identifiers from tool output structures."""
    if isinstance(value, str):
        return redact_jids_in_text(value)
    if isinstance(value, dict):
        return {key: sanitize_tool_output(item) for key, item in value.items()}
    if isinstance(value, list):
        return [sanitize_tool_output(item) for item in value]
    if isinstance(value, tuple):
        return tuple(sanitize_tool_output(item) for item in value)
    return value
