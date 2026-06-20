from app.xninetzy.db.migrations import run_migrations
from app.xninetzy.db.sqlite import init_db
from app.xninetzy.os.hitl.approval_service import request_approval, set_approval_status


def test_approval_only_admin(monkeypatch):
    init_db()
    run_migrations()
    approval_id = request_approval("chat", "sender", "test", "Title", "Summary")
    ok, msg = set_approval_status(approval_id, "approved", "user", "Regular")
    assert not ok
    assert "admin" in msg.lower()
    ok, _ = set_approval_status(approval_id, "approved", "user", "Misbahul")
    assert ok
