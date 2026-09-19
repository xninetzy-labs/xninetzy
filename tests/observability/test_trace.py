from __future__ import annotations

from xninetzy.observability.trace import (
    new_request_id,
    parse_traceparent,
    trace_from_headers,
    validate_tracestate,
)


def test_parse_traceparent_valid() -> None:
    parsed = parse_traceparent("00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01")
    assert parsed is not None
    assert parsed[0] == "0af7651916cd43dd8448eb211c80319c"
    assert parsed[1] == "b7ad6b7169203331"
    assert parsed[2] == "01"


def test_parse_traceparent_invalid() -> None:
    assert parse_traceparent("not-a-traceparent") is None
    assert parse_traceparent(None) is None
    assert parse_traceparent("") is None


def test_trace_from_headers_generates_when_missing() -> None:
    ctx = trace_from_headers({})
    assert len(ctx.trace_id) == 32
    assert len(ctx.span_id) == 16
    assert ctx.trace_flags == "01"
    assert ctx.request_id.startswith("req-")


def test_trace_from_headers_preserves_incoming() -> None:
    headers = {
        "traceparent": "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01",
        "x-request-id": "req-from-owner",
        "tracestate": "vendor=opaque",
    }
    ctx = trace_from_headers(headers)
    assert ctx.trace_id == "0af7651916cd43dd8448eb211c80319c"
    assert ctx.span_id == "b7ad6b7169203331"
    assert ctx.request_id == "req-from-owner"
    assert ctx.tracestate == "vendor=opaque"


def test_traceparent_format_in_meta() -> None:
    ctx = trace_from_headers({})
    meta = ctx.to_meta()
    assert "traceparent" in meta
    assert "request_id" in meta
    parts = meta["traceparent"].split("-")
    assert len(parts) == 4
    assert len(parts[1]) == 32
    assert len(parts[2]) == 16
    assert parts[3] in {"00", "01"}


def test_validate_tracestate_rejects_invalid_chars() -> None:
    assert validate_tracestate("vendor=ok") == "vendor=ok"
    assert validate_tracestate("has space") is None
    assert validate_tracestate("vendor=value") == "vendor=value"
    assert validate_tracestate(None) is None


def test_new_request_id_format() -> None:
    rid = new_request_id()
    assert rid.startswith("req-")
    assert len(rid) == 20
