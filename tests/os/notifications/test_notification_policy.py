from app.xninetzy.os.notifications.notification_policy import should_notify_admin


def test_source_collected_does_not_notify_admin():
    assert not should_notify_admin("deep_research_source_collected", "low")


def test_done_notifies_admin():
    assert should_notify_admin("deep_research_done", "medium")
