from __future__ import annotations

import re
import uuid
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

_TRACEPARENT_RE = re.compile(r"^([0-9a-f]{2})-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})$")
_TRACESTATE_RE = re.compile(r"^[a-z][a-z0-9_\-*/=,.]{0,255}$")

_current_request_id: ContextVar[str | None] = ContextVar("xninetzy_request_id", default=None)
_current_trace_id: ContextVar[str | None] = ContextVar("xninetzy_trace_id", default=None)
_current_span_id: ContextVar[str | None] = ContextVar("xninetzy_span_id", default=None)
_current_trace_flags: ContextVar[str | None] = ContextVar("xninetzy_trace_flags", default=None)
_current_tracestate: ContextVar[str | None] = ContextVar("xninetzy_tracestate", default=None)


@dataclass
class TraceContext:
    request_id: str
    trace_id: str
    span_id: str
    trace_flags: str = "01"
    tracestate: str | None = None

    def traceparent(self) -> str:
        return f"00-{self.trace_id}-{self.span_id}-{self.trace_flags}"

    def to_meta(self) -> dict[str, str]:
        meta = {
            "traceparent": self.traceparent(),
            "request_id": self.request_id,
        }
        if self.tracestate:
            meta["tracestate"] = self.tracestate
        return meta

    def to_dict(self) -> dict[str, str]:
        return self.to_meta()


def new_request_id() -> str:
    return f"req-{uuid.uuid4().hex[:16]}"


def parse_traceparent(value: str | None) -> tuple[str, str, str] | None:
    if not value:
        return None
    match = _TRACEPARENT_RE.match(value.strip())
    if not match:
        return None
    return match.group(2), match.group(3), match.group(4)


def validate_tracestate(value: str | None) -> str | None:
    if value is None:
        return None
    if not _TRACESTATE_RE.match(value):
        return None
    return value


def trace_from_headers(headers: dict[str, str]) -> TraceContext:
    traceparent = headers.get("traceparent")
    parsed = parse_traceparent(traceparent)
    if parsed:
        trace_id, span_id, flags = parsed
    else:
        trace_id = uuid.uuid4().hex
        span_id = uuid.uuid4().hex[:16]
        flags = "01"
    return TraceContext(
        request_id=headers.get("x-request-id") or new_request_id(),
        trace_id=trace_id,
        span_id=span_id,
        trace_flags=flags,
        tracestate=validate_tracestate(headers.get("tracestate")),
    )


def current() -> TraceContext:
    return TraceContext(
        request_id=_current_request_id.get() or new_request_id(),
        trace_id=_current_trace_id.get() or uuid.uuid4().hex,
        span_id=_current_span_id.get() or uuid.uuid4().hex[:16],
        trace_flags=_current_trace_flags.get() or "01",
        tracestate=_current_tracestate.get(),
    )


def bind(ctx: TraceContext) -> None:
    _current_request_id.set(ctx.request_id)
    _current_trace_id.set(ctx.trace_id)
    _current_span_id.set(ctx.span_id)
    _current_trace_flags.set(ctx.trace_flags)
    _current_tracestate.set(ctx.tracestate)


def reset() -> None:
    _current_request_id.set(None)
    _current_trace_id.set(None)
    _current_span_id.set(None)
    _current_trace_flags.set(None)
    _current_tracestate.set(None)


def emit(event: str, **fields: Any) -> dict[str, Any]:
    payload = {
        "event": event,
        "ts": datetime.now(timezone.utc).isoformat(),
        "request_id": _current_request_id.get(),
        "trace_id": _current_trace_id.get(),
        "span_id": _current_span_id.get(),
    }
    payload.update(fields)
    return payload
