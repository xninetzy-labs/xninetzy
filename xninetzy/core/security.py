from __future__ import annotations

import re
from typing import Any


CHAT_ID_PATTERN = re.compile(
    r"(?P<local>[A-Za-z0-9][A-Za-z0-9._:\-]*)@"
    r"(?P<domain>chat\.local|group\.local|broadcast|newsletter)\b",
    re.IGNORECASE,
)


JID_PATTERN = CHAT_ID_PATTERN


_SECRET_PATTERNS: tuple[str, ...] = (
    r"sk-[A-Za-z0-9_\-]{16,}",
    r"sk-ant-[A-Za-z0-9_\-]{16,}",
    r"ghp_[A-Za-z0-9]{16,}",
    r"github_pat_[A-Za-z0-9_]{16,}",
    r"xox[abps]-[A-Za-z0-9\-]{10,}",
    r"AIza[A-Za-z0-9_\-]{16,}",
    r"AKIA[0-9A-Z]{12,}",
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
)
_SECRET_RE = re.compile("|".join(f"(?:{p})" for p in _SECRET_PATTERNS))
_REDACTION = "[REDACTED]"


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


def redact_secrets(text: str) -> str:
    """Strip known cloud / VCS secret patterns from any text payload."""
    if not text:
        return text
    return _SECRET_RE.sub(_REDACTION, text)


def sanitize_tool_output(value: Any) -> Any:
    """Recursively redact chat identifiers AND known secrets from tool output."""
    if isinstance(value, str):
        return redact_secrets(redact_chat_ids_in_text(value))
    if isinstance(value, dict):
        return {key: sanitize_tool_output(item) for key, item in value.items()}
    if isinstance(value, list):
        return [sanitize_tool_output(item) for item in value]
    if isinstance(value, tuple):
        return tuple(sanitize_tool_output(item) for item in value)
    return value


TRUSTED_CONTEXT_DROPPED_KEYS = frozenset(
    {"chat_id", "sender_id", "sender_name", "chat_type", "group_name"}
)


def strip_trusted_context(value: Any) -> Any:
    """Drop trusted-context keys from dict outputs that would leak server identity."""
    if isinstance(value, dict):
        cleaned = {
            key: strip_trusted_context(item)
            for key, item in value.items()
            if key not in TRUSTED_CONTEXT_DROPPED_KEYS
        }
        return cleaned
    if isinstance(value, list):
        return [strip_trusted_context(item) for item in value]
    if isinstance(value, tuple):
        return tuple(strip_trusted_context(item) for item in value)
    return value
