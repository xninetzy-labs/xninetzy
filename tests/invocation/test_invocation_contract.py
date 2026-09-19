from __future__ import annotations

import pytest

from xninetzy.context.invocation.classify import (
    SIDE_EFFECT_EXTERNAL,
    SIDE_EFFECT_IDEMPOTENT_WRITE,
    SIDE_EFFECT_IRREVERSIBLE,
    SIDE_EFFECT_NON_IDEMPOTENT_WRITE,
    SIDE_EFFECT_READ_ONLY,
    SideEffectClass,
    classify_side_effect,
    side_effect_names,
)
from xninetzy.context.invocation.contract import (
    InvocationRequest,
    MAX_ARGS_BYTES,
    build_invocation_context,
    is_writing_side_effect,
    validate_invocation_request,
)
from xninetzy.context.invocation.resolve import (
    INVOCATION_FORBIDDEN_KINDS,
    resolve_invocation_route,
)
from xninetzy.context.gateway.registry import upsert_provider
from xninetzy.context.gateway.trust import (
    TRANSPORT_STDIO,
    TRUST_TIER_KNOWN_EXTERNAL,
    TRUST_TIER_UNVERIFIED,
)


def test_side_effect_names_covers_all_classes():
    names = set(side_effect_names())
    assert {
        SIDE_EFFECT_READ_ONLY,
        SIDE_EFFECT_IDEMPOTENT_WRITE,
        SIDE_EFFECT_NON_IDEMPOTENT_WRITE,
        SIDE_EFFECT_EXTERNAL,
        SIDE_EFFECT_IRREVERSIBLE,
    }.issubset(names)


def test_classify_side_effect_unknown_defaults_read_only():
    cls = classify_side_effect("not-a-real-class")
    assert isinstance(cls, SideEffectClass)
    assert cls.name == SIDE_EFFECT_READ_ONLY


def test_classify_side_effect_none_defaults_read_only():
    cls = classify_side_effect(None)
    assert cls.name == SIDE_EFFECT_READ_ONLY


def test_classify_side_effect_irreversible_requires_approval():
    cls = classify_side_effect(SIDE_EFFECT_IRREVERSIBLE)
    assert cls.requires_approval is True
    assert cls.requires_idempotency_key is True
    assert cls.allowed_for_unverified is False


def test_classify_side_effect_idempotent_write_allows_unverified():
    cls = classify_side_effect(SIDE_EFFECT_IDEMPOTENT_WRITE)
    assert cls.requires_idempotency_key is True
    assert cls.requires_approval is False
    assert cls.allowed_for_unverified is True


def test_is_writing_side_effect_classification():
    assert is_writing_side_effect(SIDE_EFFECT_READ_ONLY) is False
    assert is_writing_side_effect(SIDE_EFFECT_IDEMPOTENT_WRITE) is True
    assert is_writing_side_effect(SIDE_EFFECT_NON_IDEMPOTENT_WRITE) is True
    assert is_writing_side_effect(SIDE_EFFECT_EXTERNAL) is True
    assert is_writing_side_effect(SIDE_EFFECT_IRREVERSIBLE) is True


def _make_request(**overrides):
    base = dict(
        request_id="req-1",
        intent="intent-x",
        capability="do_thing",
        context_key="ctx",
        query="please",
        args=(("k", "v"),),
        side_effect=SIDE_EFFECT_READ_ONLY,
        idempotency_key=None,
        approval_id=None,
    )
    base.update(overrides)
    return InvocationRequest(**base)


def test_validate_request_rejects_missing_request_id():
    req = _make_request(request_id="")
    with pytest.raises(ValueError):
        validate_invocation_request(req)


def test_validate_request_rejects_missing_capability():
    req = _make_request(capability="")
    with pytest.raises(ValueError):
        validate_invocation_request(req)


def test_validate_request_rejects_missing_context_key():
    req = _make_request(context_key="")
    with pytest.raises(ValueError):
        validate_invocation_request(req)


def test_validate_request_rejects_missing_intent():
    req = _make_request(intent="")
    with pytest.raises(ValueError):
        validate_invocation_request(req)


def test_validate_request_requires_idempotency_for_writes():
    req = _make_request(side_effect=SIDE_EFFECT_IDEMPOTENT_WRITE, idempotency_key=None)
    with pytest.raises(ValueError):
        validate_invocation_request(req)


def test_validate_request_accepts_irreversible_without_approval_id_as_flag():
    req = _make_request(
        side_effect=SIDE_EFFECT_IRREVERSIBLE,
        idempotency_key="idem-1",
        approval_id=None,
    )
    validate_invocation_request(req)


def test_validate_request_accepts_irreversible_with_approval():
    req = _make_request(
        side_effect=SIDE_EFFECT_IRREVERSIBLE,
        idempotency_key="idem-1",
        approval_id=42,
    )
    validate_invocation_request(req)


def test_validate_request_rejects_oversized_args():
    big_value = "x" * (MAX_ARGS_BYTES + 1)
    req = _make_request(args=(("k", big_value),))
    with pytest.raises(ValueError):
        validate_invocation_request(req)


def test_build_invocation_context_returns_populated_context():
    req = _make_request(side_effect=SIDE_EFFECT_IDEMPOTENT_WRITE, idempotency_key="k1")
    ctx = build_invocation_context(req)
    assert ctx.request is req
    assert ctx.side_effect_class.name == SIDE_EFFECT_IDEMPOTENT_WRITE
    assert ctx.args_bytes > 0
    assert len(ctx.args_hash) == 64


def test_build_invocation_context_is_idempotent_for_args():
    req1 = _make_request(args=(("k", "v"),))
    req2 = _make_request(args=(("k", "v"),))
    ctx1 = build_invocation_context(req1)
    ctx2 = build_invocation_context(req2)
    assert ctx1.args_hash == ctx2.args_hash


def test_resolve_invocation_route_uses_local_self_when_no_provider(
    tmp_path, monkeypatch
):
    db = tmp_path / "inv.db"
    monkeypatch.setenv("SQLITE_PATH", str(db))
    from xninetzy.core import config as cfg
    from xninetzy.db.migrations import run_migrations
    from xninetzy.context.capability_graph.graph import seed_from_registry

    cfg.get_settings.cache_clear()
    run_migrations()
    seed_from_registry()
    req = _make_request()
    route = resolve_invocation_route(req, include_local_self=False)
    assert route.decision.chosen is None
    assert route.min_trust_tier >= TRUST_TIER_UNVERIFIED


def test_resolve_invocation_route_surfaces_eligible_providers_unfiltered(
    tmp_path, monkeypatch
):
    db = tmp_path / "inv.db"
    monkeypatch.setenv("SQLITE_PATH", str(db))
    from xninetzy.core import config as cfg
    from xninetzy.db.migrations import run_migrations
    from xninetzy.context.capability_graph.graph import seed_from_registry

    cfg.get_settings.cache_clear()
    run_migrations()
    seed_from_registry()
    upsert_provider(
        provider_id="trusted",
        transport=TRANSPORT_STDIO,
        endpoint="cmd",
        trust_tier=TRUST_TIER_KNOWN_EXTERNAL,
        risk_class="low",
        capabilities=("do_thing",),
    )
    req = _make_request(
        capability="do_thing",
        side_effect=SIDE_EFFECT_NON_IDEMPOTENT_WRITE,
        idempotency_key="idem-w",
    )
    route = resolve_invocation_route(req)
    assert any(p.provider_id == "trusted" for p in route.eligible_providers)


def test_resolve_invocation_route_includes_unverified_for_policy_gate(
    tmp_path, monkeypatch
):
    db = tmp_path / "inv.db"
    monkeypatch.setenv("SQLITE_PATH", str(db))
    from xninetzy.core import config as cfg
    from xninetzy.db.migrations import run_migrations
    from xninetzy.context.capability_graph.graph import seed_from_registry

    cfg.get_settings.cache_clear()
    run_migrations()
    seed_from_registry()
    upsert_provider(
        provider_id="unverified",
        transport=TRANSPORT_STDIO,
        endpoint="cmd",
        trust_tier=TRUST_TIER_UNVERIFIED,
        risk_class="unreviewed",
        capabilities=("do_thing",),
    )
    req = _make_request(
        side_effect=SIDE_EFFECT_NON_IDEMPOTENT_WRITE,
        idempotency_key="idem-w",
        capability="do_thing",
    )
    route = resolve_invocation_route(req, include_local_self=False)
    assert any(p.provider_id == "unverified" for p in route.eligible_providers)


def test_invocation_forbidden_kinds_default_empty():
    assert isinstance(INVOCATION_FORBIDDEN_KINDS, frozenset)
