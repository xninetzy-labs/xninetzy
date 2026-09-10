"""Performance regression: hebat_sync_assignments must not timeout on 120 assignments."""

import asyncio
import time
from unittest.mock import patch

import pytest


@pytest.mark.asyncio
async def test_sync_handles_many_without_timeout():
    from xninetzy.os.academic.hebat.tools import hebat_sync_assignments

    # Mock list_activities to return 20 assignments (scale test)
    mock_activities = [
        {"cmid": str(1000 + i), "id": 2000 + i, "title": f"Tugas {i}"}
        for i in range(20)
    ]

    mock_detail = {
        "title": "Tugas X",
        "instruction": "instr",
        "opened_at": "9 February 2026, 3:00 PM",
        "due_at": "2 March 2026, 5:00 PM",
        "time_remaining": "10 days remaining",
        "submission_status": "No submissions have been made yet",
        "grading_status": "Not graded",
        "last_modified": "-",
    }

    async def fake_fetch(chat_id, cmid):
        await asyncio.sleep(0.02)  # simulate network
        return mock_detail

    with patch("xninetzy.os.academic.hebat.tools.list_activities", return_value=mock_activities), patch(
        "xninetzy.os.academic.hebat.tools.fetch_assignment_detail", side_effect=fake_fetch
    ), patch("xninetzy.os.academic.hebat.tools.upsert_assignment", return_value=999), patch(
        "xninetzy.os.academic.hebat.tools.sync_assignment_task", return_value=(1, True)
    ), patch(
        "xninetzy.os.academic.hebat.tools.has_reminder_for_assignment", return_value=True
    ), patch(
        "xninetzy.os.academic.hebat.tools._ensure_session_or_msg", return_value=None
    ), patch(
        "xninetzy.os.academic.hebat.tools.get_settings"
    ) as mock_settings:
        # Use small rate limit for test; old sequential would be 20*0.2=4s, new concurrent ~0.8s
        class S:
            HEBAT_RATE_LIMIT_SECONDS = 0.1

            def hebat_reminder_hours(self):
                return [24]

            APP_TIMEZONE = "Asia/Jakarta"

        mock_settings.return_value = S()

        start = time.time()
        result = await hebat_sync_assignments.ainvoke({"chat_id": "dummy_chat_id", "course_id": None})
        elapsed = time.time() - start

        assert "Sync assignment selesai" in result
        # With concurrency=5, 20 items with 0.02s fetch + 0.02s sleep should be <2s, sequential would be >2s with 0.1 sleep each (2s)
        # Allow 3s threshold for CI
        assert elapsed < 3.0, f"sync took {elapsed:.2f}s, expected <3s with concurrency; possible sequential blocking"
