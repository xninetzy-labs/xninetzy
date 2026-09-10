from __future__ import annotations

import pytest

from app.xninetzy.db.idempotency import (
    IDEMPOTENCY_INDEX_DDL,
    IDEMPOTENCY_TABLE_DDL,
    idempotent_call,
    storage_key,
)
from app.xninetzy.db.sqlite import connect


@pytest.fixture(autouse=True)
def _clean_idempotency_table():
    with connect() as conn:
        conn.execute(IDEMPOTENCY_TABLE_DDL)
        conn.execute(IDEMPOTENCY_INDEX_DDL)
        conn.execute("DELETE FROM idempotency_keys")
    yield


def test_storage_key_deterministic_and_payload_sensitive():
    first = storage_key("task_capture", "abc", {"title": "A"})
    again = storage_key("task_capture", "abc", {"title": "A"})
    other_payload = storage_key("task_capture", "abc", {"title": "B"})
    other_scope = storage_key("task_list", "abc", {"title": "A"})
    assert first == again
    assert first != other_payload
    assert first != other_scope


def test_call_without_key_executes_every_time():
    counter = {"n": 0}

    def run() -> str:
        counter["n"] += 1
        return f"run-{counter['n']}"

    assert idempotent_call("scope", "", {}, run) == ("run-1", True)
    assert idempotent_call("scope", None, {}, run) == ("run-2", True)


def test_same_key_replays_stored_result_without_reexecution():
    counter = {"n": 0}

    def run() -> str:
        counter["n"] += 1
        return f"result-{counter['n']}"

    first, created_first = idempotent_call("scope", "key-1", {"a": 1}, run)
    replay, created_replay = idempotent_call("scope", "key-1", {"a": 1}, run)

    assert created_first is True
    assert created_replay is False
    assert first == replay == "result-1"
    assert counter["n"] == 1


def test_different_key_or_payload_executes_again():
    counter = {"n": 0}

    def run() -> int:
        counter["n"] += 1
        return counter["n"]

    assert idempotent_call("scope", "key-a", {}, run)[1] is True
    assert idempotent_call("scope", "key-b", {}, run)[1] is True
    assert idempotent_call("scope", "key-a", {"x": 1}, run)[1] is True
    assert counter["n"] == 3


def test_failed_execution_releases_reservation_for_retry():
    attempts = {"n": 0}

    def flaky() -> str:
        attempts["n"] += 1
        if attempts["n"] == 1:
            raise RuntimeError("boom")
        return "recovered"

    with pytest.raises(RuntimeError):
        idempotent_call("scope", "flaky", {}, flaky)

    result, created = idempotent_call("scope", "flaky", {}, flaky)
    assert result == "recovered"
    assert created is True


@pytest.mark.asyncio
async def test_task_capture_with_idempotency_key_does_not_duplicate(monkeypatch):
    from app.xninetzy.tools.ecosystem import life_tools

    monkeypatch.setattr(life_tools, "record_event", lambda *args, **kwargs: None)

    first = await life_tools.task_capture.ainvoke(
        {
            "title": "Belajar RAG",
            "chat_id": "chat-test",
            "idempotency_key": "retry-42",
        }
    )
    replay = await life_tools.task_capture.ainvoke(
        {
            "title": "Belajar RAG",
            "chat_id": "chat-test",
            "idempotency_key": "retry-42",
        }
    )
    fresh = await life_tools.task_capture.ainvoke(
        {
            "title": "Belajar RAG",
            "chat_id": "chat-test",
        }
    )

    assert first == replay
    assert fresh != first


def test_knowledge_ingest_text_idempotent_via_key(monkeypatch):
    from app.xninetzy.os.knowledge import ingestion as knowledge_ingestion
    from app.xninetzy.tools.ecosystem import knowledge_tools

    calls = {"n": 0}

    def fake_ingest(title, text, source_type, uri):
        calls["n"] += 1
        return {"status": "ok", "chunks": 3, "source_id": f"src-{calls['n']}"}

    monkeypatch.setattr(knowledge_ingestion, "ingest_text", fake_ingest)
    monkeypatch.setattr(knowledge_tools, "record_event", lambda *args, **kwargs: None)

    args = {
        "title": "Catatan",
        "text": "isi materi",
        "source_type": "manual_note",
        "idempotency_key": "ingest-7",
    }
    first = knowledge_tools.knowledge_ingest_text.invoke(args)
    replay = knowledge_tools.knowledge_ingest_text.invoke(args)

    assert first == replay
    assert calls["n"] == 1
