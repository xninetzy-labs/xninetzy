from app.xninetzy.db.migrations import run_migrations
from app.xninetzy.db.sqlite import init_db
from app.xninetzy.os.rules.store import (
    add_rule,
    classify_rule,
    delete_rule,
    format_rules_for_prompt,
    get_active_rules,
    list_rules,
    search_rules,
    set_active,
)

U = "rules-test-user"


def _setup():
    init_db()
    run_migrations()


def test_classify_rule():
    assert classify_rule("jangan kirim reminder malam") == "dont"
    assert classify_rule("selalu cek memory dulu") == "do"
    assert classify_rule("jawab dengan gaya santai") == "style"
    assert classify_rule("jangan auto-submit tugas HEBAT") == "safety"


def test_add_and_get_active_rules():
    _setup()
    u = U + "-1"
    r = add_rule(u, "jangan jawab panjang kalau aku minta singkat")
    assert r["id"] > 0
    active = get_active_rules(u)
    assert any(x["id"] == r["id"] for x in active)


def test_disable_then_excluded_from_active():
    _setup()
    u = U + "-2"
    r = add_rule(u, "selalu kasih contoh praktis")
    assert set_active(u, r["id"], False) is True
    active = get_active_rules(u)
    assert all(x["id"] != r["id"] for x in active)
    # but still listed when not active_only
    assert any(x["id"] == r["id"] for x in list_rules(u))


def test_delete_rule():
    _setup()
    u = U + "-3"
    r = add_rule(u, "jangan tag semua orang")
    assert delete_rule(u, r["id"]) is True
    assert all(x["id"] != r["id"] for x in list_rules(u))


def test_search_rules():
    _setup()
    u = U + "-4"
    add_rule(u, "kalau coding kasih langkah praktis dulu")
    rows = search_rules(u, "coding")
    assert rows and "coding" in rows[0]["content"]


def test_format_rules_for_prompt():
    rules = [{"rule_type": "dont", "content": "jangan spam"}]
    out = format_rules_for_prompt(rules)
    assert "jangan spam" in out and "Aturan dari user" in out
    assert format_rules_for_prompt([]) == ""


def test_safety_priority_higher():
    _setup()
    u = U + "-5"
    r = add_rule(u, "jangan auto-submit tugas HEBAT")
    row = [x for x in list_rules(u) if x["id"] == r["id"]][0]
    assert row["rule_type"] == "safety"
    assert row["priority"] >= 90
