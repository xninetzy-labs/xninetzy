from __future__ import annotations

from xninetzy.context.routing.lazy_schema import (
    MAX_FULL_SCHEMA_BYTES,
    MAX_LIGHT_METADATA_BYTES,
    MAX_TOTAL_BUDGET_BYTES,
    materialize_schemas,
)


def test_constants_boundaries() -> None:
    assert MAX_FULL_SCHEMA_BYTES >= 4_000
    assert MAX_LIGHT_METADATA_BYTES <= 2_048
    assert MAX_TOTAL_BUDGET_BYTES >= 32_000


def test_materialize_schemas_handles_chosen_only() -> None:
    b = materialize_schemas("knowledge_search")
    assert b.primary_tool == "knowledge_search"
    assert b.alternates == ()
    assert b.total_bytes > 0


def test_materialize_schemas_keeps_within_budget() -> None:
    alts = tuple(f"tool_alias_{i}_{'x' * 50}" for i in range(8))
    b = materialize_schemas("knowledge_search", alternates=alts)
    assert b.total_bytes <= MAX_TOTAL_BUDGET_BYTES * 2 + 4096
    assert len(b.omitted) >= 0


def test_materialize_schemas_truncates_when_oversized() -> None:
    alts = tuple(f"tool_{i}_{'y' * 1000}" for i in range(15))
    b = materialize_schemas("knowledge_search", alternates=alts)
    assert b.truncation_applied or len(b.alternates) <= 5
