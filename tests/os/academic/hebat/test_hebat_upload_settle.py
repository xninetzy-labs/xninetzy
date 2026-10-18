from __future__ import annotations

import pytest

from xninetzy.os.academic.hebat import submission
from xninetzy.os.academic.hebat.submission import (
    _click_save,
    _save_failure_reason,
    _upload_state,
    _wait_for_upload_listed,
)

NAME = "187241037_Misbahul_Integration.pdf"


def snap(names=(), errors=(), updating=False, dialog_open=False, edit_form_open=False):
    return {
        "names": list(names),
        "errors": list(errors),
        "updating": updating,
        "dialogOpen": dialog_open,
        "editFormOpen": edit_form_open,
    }


def test_upload_state_pending_when_file_not_listed():
    assert _upload_state(snap(), NAME, [], [])[0] == "pending"


def test_upload_state_ready_when_listed_and_idle():
    assert _upload_state(snap([NAME]), NAME, [], []) == ("ready", None)


def test_upload_state_waits_while_filemanager_updating():
    assert _upload_state(snap([NAME], updating=True), NAME, [], [])[0] == "pending"


def test_upload_state_waits_while_dialog_open():
    assert _upload_state(snap([NAME], dialog_open=True), NAME, [], [])[0] == "pending"


def test_upload_state_ready_for_second_file_in_same_submission():
    first = "first.pdf"
    assert _upload_state(snap([first, NAME]), NAME, [first], [])[0] == "ready"


def test_upload_state_same_name_already_present_is_not_ready():
    assert _upload_state(snap([NAME]), NAME, [NAME], [])[0] == "pending"


def test_upload_state_counts_new_entry_even_if_server_renames_file():
    assert _upload_state(snap(["renamed.pdf"]), NAME, [], [])[0] == "ready"


def test_upload_state_reports_new_errors():
    state, detail = _upload_state(snap(errors=["File too large"]), NAME, [], [])
    assert state == "error"
    assert "File too large" in detail


def test_upload_state_ignores_preexisting_errors():
    assert _upload_state(snap([NAME], errors=["Banner"]), NAME, [], ["Banner"]) == ("ready", None)


class _SnapshotPage:
    def __init__(self, snapshots):
        self.snapshots = list(snapshots)
        self.calls = 0

    async def evaluate(self, script):
        self.calls += 1
        return self.snapshots[min(self.calls - 1, len(self.snapshots) - 1)]


@pytest.mark.asyncio
async def test_wait_for_upload_listed_polls_until_ready():
    page = _SnapshotPage([snap(), snap(updating=True), snap([NAME])])
    result = await _wait_for_upload_listed(page, NAME, [], [], timeout_s=5, poll_interval_s=0)
    assert result == ("ready", None)
    assert page.calls == 3


@pytest.mark.asyncio
async def test_wait_for_upload_listed_times_out():
    page = _SnapshotPage([snap()])
    state, detail = await _wait_for_upload_listed(
        page, NAME, [], [], timeout_s=0.05, poll_interval_s=0.01
    )
    assert state == "timeout"
    assert "belum muncul" in detail


@pytest.mark.asyncio
async def test_wait_for_upload_listed_stops_on_error():
    page = _SnapshotPage([snap(), snap(errors=["Upload failed"])])
    state, detail = await _wait_for_upload_listed(
        page, NAME, [], [], timeout_s=5, poll_interval_s=0
    )
    assert state == "error"
    assert "Upload failed" in detail


def test_save_failure_reason_none_when_form_closed():
    assert _save_failure_reason(snap(edit_form_open=False)) is None


def test_save_failure_reason_reports_moodle_error():
    reason = _save_failure_reason(snap(errors=["Invalid file"], edit_form_open=True))
    assert "Moodle menolak" in reason
    assert "Invalid file" in reason


def test_save_failure_reason_generic_when_form_still_open():
    assert "masih terbuka" in _save_failure_reason(snap(edit_form_open=True))


class _Navigation:
    def __init__(self, log):
        self.log = log

    async def __aenter__(self):
        self.log.append("nav_enter")

    async def __aexit__(self, *exc):
        self.log.append("nav_exit")
        return False


class _Button:
    def __init__(self, log):
        self.log = log

    async def click(self, timeout=None):
        self.log.append("click")


class _Form:
    def __init__(self, log):
        self.log = log

    async def evaluate(self, script):
        self.log.append("form_submit")


class _SavePage:
    def __init__(self, has_button):
        self.has_button = has_button
        self.log = []

    def expect_navigation(self, **kwargs):
        self.log.append("expect_navigation")
        return _Navigation(self.log)

    async def wait_for_selector(self, selector, state=None, timeout=None):
        if selector == submission.SAVE_SELECTOR:
            if not self.has_button:
                raise submission.PlaywrightTimeoutError("save button missing")
            return _Button(self.log)
        return _Form(self.log)


@pytest.mark.asyncio
async def test_click_save_clicks_inside_navigation_wait():
    page = _SavePage(has_button=True)
    await _click_save(page)
    assert page.log == ["expect_navigation", "nav_enter", "click", "nav_exit"]


@pytest.mark.asyncio
async def test_click_save_falls_back_to_form_submit_inside_navigation_wait():
    page = _SavePage(has_button=False)
    await _click_save(page)
    assert page.log == ["expect_navigation", "nav_enter", "form_submit", "nav_exit"]
