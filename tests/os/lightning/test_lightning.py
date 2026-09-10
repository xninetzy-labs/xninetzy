from app.xninetzy.db.migrations import run_migrations
from app.xninetzy.db.sqlite import init_db
from app.xninetzy.os.lightning.feedback_parser import classify_feedback
from app.xninetzy.os.lightning.service import apply_proposal, reject_proposal, submit_feedback
from app.xninetzy.os.lightning.store import latest_trace, list_proposals, log_trace


def _setup():
    init_db()
    run_migrations()


def test_log_and_latest_trace():
    _setup()
    chat = "trace-chat-1"
    tid = log_trace(user_id="u", chat_id=chat, message_id="m1",
                    input_text="halo", response_text="hai", intent="direct",
                    tools_used=["datetime_now"])
    assert tid.startswith("T-")
    t = latest_trace(chat)
    assert t and t["trace_id"] == tid
    assert "datetime_now" in t["tools_used_json"]


def test_classify_feedback():
    assert classify_feedback("makasih, mantap")["feedback_type"] == "praise"
    c = classify_feedback("tadi kepanjangan, harusnya ringkas")
    assert c["feedback_type"] == "correction"
    assert c["implies_change"] is True
    assert c["suggested_rule"]


def test_feedback_creates_proposal():
    _setup()
    chat = "fb-chat-1"
    out = submit_feedback("user-fb", chat, "harusnya kasih langkah dulu baru teori")
    assert "Proposal" in out
    pending = list_proposals(status="pending")
    assert any(p["target_area"] == "rule" for p in pending)


def test_praise_no_proposal():
    _setup()
    out = submit_feedback("user-fb2", "fb-chat-2", "keren makasih")
    assert "makasih" in out.lower() or "🙏" in out


def test_approve_requires_admin_and_applies_rule():
    _setup()
    chat = "fb-chat-3"
    submit_feedback("owner-jid", chat, "jangan jawab panjang kalau aku minta singkat")
    prop = list_proposals(status="pending")[0]

    # non-admin rejected
    out = apply_proposal(prop["id"], "random", "Random User")
    assert "admin" in out.lower()

    # admin applies -> creates a rule
    out2 = apply_proposal(prop["id"], "owner-jid", "Misbahul")
    assert "disetujui" in out2.lower()
    from app.xninetzy.os.rules.store import list_rules
    rules = list_rules("owner-jid")
    assert any("panjang" in r["content"].lower() or "singkat" in r["content"].lower() for r in rules)


def test_reject_proposal_admin():
    _setup()
    chat = "fb-chat-4"
    submit_feedback("u4", chat, "harusnya pakai contoh nyata")
    prop = list_proposals(status="pending")[0]
    out = reject_proposal(prop["id"], "u4", "Misbahul")
    assert "ditolak" in out.lower()
