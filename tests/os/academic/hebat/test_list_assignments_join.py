"""Regression for list_assignments JOIN — cmid vs id mismatch."""

from xninetzy.db.sqlite import connect, init_db
from xninetzy.os.academic.hebat.models import ActivityType, HebatActivity, HebatAssignment
from xninetzy.os.academic.hebat.storage import list_assignments, upsert_activity, upsert_assignment


def _clean():
    init_db()
    with connect() as conn:
        conn.execute("DELETE FROM hebat_assignments WHERE title='Tugas 2 SII208 JOIN TEST'")
        conn.execute("DELETE FROM hebat_activities WHERE cmid='105393' AND title='Tugas 2 SII208 JOIN TEST'")


def test_list_assignments_finds_by_cmid_mismatch():
    _clean()
    init_db()
    act = HebatActivity(
        course_id="10927",
        cmid="105393",
        type=ActivityType.ASSIGN,
        title="Tugas 2 SII208 JOIN TEST",
        section_title="Minggu 2",
        activity_url="https://hebat.elearning.unair.ac.id/mod/assign/view.php?id=105393",
    )
    upsert_activity(act)  # autoincrement id, e.g. 999
    # Simulate legacy data where assignment activity_id was stored as cmid string 105393
    assign = HebatAssignment(
        activity_id=105393,
        title="Tugas 2 SII208 JOIN TEST",
        instruction_text="instr",
        opened_at=None,
        due_at=None,
        time_remaining_text=None,
        submission_status="No submissions have been made yet",
        grading_status="Not graded",
        last_modified_text="-",
    )
    upsert_assignment(assign)
    try:
        listed = list_assignments()
        found = [x for x in listed if x["title"] == "Tugas 2 SII208 JOIN TEST"]
        assert len(found) == 1, f"expected 1, got {len(found)} — join should find via cmid"
        assert str(found[0]["cmid"]) == "105393"
        # Also check that DISTINCT prevents duplicate when both branches would match (if we artificially set act.id == 105393)
        # Not needed as autoincrement won't equal 105393, but ensure no dup
        ids = [x["id"] for x in found]
        assert len(ids) == len(set(ids))
    finally:
        _clean()


def test_no_duplicate_when_both_conditions_match():
    _clean()
    init_db()
    # Create activity where cmid equals id to test OR duplicate
    with connect() as conn:
        conn.execute(
            "INSERT INTO hebat_activities (course_id, cmid, type, title, section_title, activity_url, last_synced_at) VALUES (?, ?, ?, ?, ?, ?, datetime('now'))",
            ("10927", "7777", "assign", "Tugas Dup TEST", "Minggu X", "https://example.com/mod/assign/view.php?id=7777"),
        )
        row = conn.execute("SELECT id FROM hebat_activities WHERE cmid='7777' LIMIT 1").fetchone()
        act_id = row["id"]
        conn.execute("UPDATE hebat_activities SET cmid=? WHERE id=?", (str(act_id), act_id))
        conn.execute(
            "INSERT INTO hebat_assignments (activity_id, title, submission_status, grading_status, last_synced_at) VALUES (?, ?, ?, ?, datetime('now'))",
            (act_id, "Tugas Dup TEST", "No submissions", "Not graded"),
        )
    # Now list should return exactly 1, not 2 duplicates (open new connection)
    lst = list_assignments()
    found = [x for x in lst if x["title"] == "Tugas Dup TEST"]
    assert len(found) == 1, f"duplicate rows: {found} (act_id={act_id})"
    # cleanup
    with connect() as conn:
        conn.execute("DELETE FROM hebat_assignments WHERE title='Tugas Dup TEST'")
        conn.execute("DELETE FROM hebat_activities WHERE title='Tugas Dup TEST'")
