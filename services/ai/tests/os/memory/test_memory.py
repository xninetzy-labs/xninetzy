from app.xninetzy.db.migrations import run_migrations
from app.xninetzy.db.sqlite import init_db
from app.xninetzy.os.memory.memory_store import (
    add_memory,
    classify_memory,
    forget_memory,
    format_memories_for_prompt,
    list_memories,
    search_memories,
    update_memory,
)

U = "mem-test-user"


def _setup():
    init_db()
    run_migrations()


def test_classify_memory():
    assert classify_memory("aku lagi belajar APSI") == "learning_profile"
    assert classify_memory("aku suka jawaban ringkas") == "preference"
    assert classify_memory("lagi ngerjain project xninetzy") == "project_context"


def test_add_and_list():
    _setup()
    u = U + "-1"
    m = add_memory(u, "aku lagi belajar Graph RAG")
    assert m["id"] > 0
    assert any(x["id"] == m["id"] for x in list_memories(u))


def test_search_finds_relevant():
    _setup()
    u = U + "-2"
    add_memory(u, "aku belajar jaringan komputer")
    add_memory(u, "aku suka kopi tanpa gula")
    rows = search_memories(u, "jaringan komputer")
    assert rows
    assert any("jaringan" in r["content"] for r in rows)


def test_update_and_forget():
    _setup()
    u = U + "-3"
    m = add_memory(u, "deadline APSI minggu depan")
    assert update_memory(u, m["id"], "deadline APSI hari Jumat") is True
    assert forget_memory(u, m["id"]) is True
    assert all(x["id"] != m["id"] for x in list_memories(u, active_only=True))


def test_format_for_prompt():
    rows = [{"memory_type": "preference", "content": "suka ringkas"}]
    out = format_memories_for_prompt(rows)
    assert "suka ringkas" in out and "Memory tentang user" in out
    assert format_memories_for_prompt([]) == ""
