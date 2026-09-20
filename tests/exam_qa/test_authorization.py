from __future__ import annotations

import pytest

from xninetzy.context.exam_qa.provider import (
    PROVIDER_LOCAL,
    PROVIDER_MOCK,
    list_providers,
    resolve_provider,
)
from xninetzy.context.exam_qa.scenario import (
    SCENARIO_EXAM,
    build_scenario,
)
from xninetzy.db.sqlite import connect
from xninetzy.os.exam_qa.environment import capture_environment
from xninetzy.os.exam_qa.evidence import (
    build_evidence_bundle,
    evidence_to_row,
    load_evidence_for_run,
)


def test_resolve_provider_known_and_unknown():
    mock = resolve_provider(PROVIDER_MOCK)
    assert mock.offline_only
    local = resolve_provider(PROVIDER_LOCAL)
    assert local.provider_id == PROVIDER_LOCAL
    with pytest.raises(ValueError):
        resolve_provider("nope")


def test_list_providers_sorted():
    ids = tuple(p.provider_id for p in list_providers())
    assert ids == (PROVIDER_LOCAL, PROVIDER_MOCK)


def test_authorization_table_supports_grants(tmp_path, monkeypatch):
    monkeypatch.setenv("XNINETZY_EXAM_OFFLINE", "1")
    scenario = build_scenario(
        scenario_id="sc1",
        fixture_id="f1",
        kind=SCENARIO_EXAM,
        time_limit_minutes=30,
        pass_threshold=0.6,
        authorized=True,
    )
    with connect() as conn:
        conn.execute(
            "INSERT INTO test_accounts (account_id, label, scopes, created_at) "
            "VALUES (?, ?, ?, ?)",
            ("acc-1", "owner", '["scenario:exam"]', "2026-09-20T00:00:00Z"),
        )
        conn.execute(
            "INSERT INTO exam_authorization (account_id, scenario_id, approval_id, granted_at) "
            "VALUES (?, ?, ?, ?)",
            ("acc-1", scenario.scenario_id, 99, "2026-09-20T00:00:00Z"),
        )
        conn.commit()
        row = conn.execute(
            "SELECT approval_id FROM exam_authorization WHERE account_id = ? AND scenario_id = ?",
            ("acc-1", scenario.scenario_id),
        ).fetchone()
    assert row["approval_id"] == 99


def test_evidence_roundtrip():
    bundle = build_evidence_bundle(
        run_id="run-1",
        question_id="q1",
        expected_answer="a",
        actual_answer="a",
        score=1.0,
        keywords=("a",),
        captured_at="2026-09-20T00:00:00Z",
    )
    with connect() as conn:
        conn.execute(
            "INSERT INTO evidence_artifacts "
            "(run_id, question_id, expected_answer, actual_answer, score, captured_at, payload_json) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            evidence_to_row(bundle),
        )
        conn.commit()
    loaded = load_evidence_for_run("run-1")
    assert len(loaded) == 1
    assert loaded[0].score == 1.0


def test_environment_capture_offline(monkeypatch):
    monkeypatch.setenv("XNINETZY_EXAM_SANDBOX", "true")
    snap = capture_environment(now="2026-09-20T00:00:00Z")
    assert snap.sandboxed is True
    assert snap.offline_only is True
    payload = snap.as_dict()
    assert payload["captured_at"] == "2026-09-20T00:00:00Z"