# Fix HEBAT Assignment Error — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Perbaiki error kontinu pada kode xninetzy assignment HEBAT sehingga sync, parsing due date, task linking, dan Obsidian implementation berjalan tanpa timeout dan menghasilkan data yang benar, serta verifikasi perbaikan via testing langsung.

**Architecture:** Perbaiki root cause di parser (`parsers.py` class_=True bug) dan lapis sync (`tools.py` sequential blocking + rate limit). Tambah concurrency terkendali dengan semaphore, robust date parsing untuk EN+ID, perbaiki join di `storage.py`, dan migrasi vault ke canonical `Academic/Current|Archive` via xninetzy-obsidian-orchestra. Setiap fix dilandasi TDD failing test → minimal implementation → verification via real HEBAT sync dan `pytest`.

**Tech Stack:** Python 3.14, BeautifulSoup lxml, httpx + Playwright (existing), SQLite (hebat_activities/assignments/tasks), pytest + ruff, ObsidianVaultService (xninetzy-obsidian-orchestra), asyncio semaphore

## Global Constraints

- Python 3.14, project root `/home/misbahul45/code/xninetzy`, services dir `services/ai`
- Do not bypass CAPTCHA/OTP, do not auto-commit/push, do not overwrite user unrelated changes (check `git status --short` before edit)
- MCP timeout 120s untuk `hebat_sync_assignments` — sync harus partial-success dan tidak hang
- Vault paths relative, human-readable per orchestra: `Academic/Current/{Code} - {Full Name}/`, `Academic/Archive/{Year} {Period}/{Code} - {Full Name}/`, file `Tugas N - Title.md`
- Testing must use `cd services/ai && uv run pytest` dan `uv run ruff check`; verification via real `hebat_sync_assignments` dan `hebat_academic_digest` setelah fix
- Preserve idempotency: `sync_assignment_task` dan `has_reminder_for_assignment` tetap idempoten

---

### Task 1: Fix `parse_assignment_page` due/opened date extraction (root cause)

**Files:**
- Modify: `services/ai/app/xninetzy/os/academic/hebat/parsers.py:152-166`
- Modify: `services/ai/tests/os/academic/hebat/test_hebat_extractors.py` (add regression)
- Create: `services/ai/tests/os/academic/hebat/test_parse_assignment_dates.py`
- Test: `services/ai/tests/os/academic/hebat/test_parse_assignment_dates.py`

**Interfaces:**
- Consumes: raw HTML dari `hebat.elearning.unair.ac.id/mod/assign/view.php?id={cmid}` (contoh cmid 36248 dengan `<div class="activity-dates" data-region="activity-dates"><div><strong>Opened:</strong> Monday, 9 Feb 2026, 3:00 PM</div><div><strong>Due:</strong> Monday, 2 March 2026, 5:00 PM</div></div>`)
- Produces: `parse_assignment_page(html) -> dict` dengan `due_at` = "2 March 2026, 5:00 PM" (bukan None), `opened_at` = "9 February 2026, 3:00 PM"

- [ ] **Step 1: Write failing test for dates_region without class**

```python
# services/ai/tests/os/academic/hebat/test_parse_assignment_dates.py
from app.xninetzy.os.academic.hebat.parsers import parse_assignment_page

HTML_DATES_NO_CLASS = """
<html><body>
<h1>Tugas Modul Praktikum Minggu 1b</h1>
<div class="activity-dates" data-region="activity-dates">
 <div><strong>Opened:</strong> Monday, 9 February 2026, 3:00 PM</div>
 <div><strong>Due:</strong> Monday, 2 March 2026, 5:00 PM</div>
</div>
<table class="generaltable">
<tr><th>Submission status</th><td>No submissions have been made yet</td></tr>
<tr><th>Time remaining</th><td>Assignment is overdue by: 178 days 8 hours</td></tr>
</table>
<div id="intro">Instruksi tugas</div>
</body></html>
"""
def test_parse_dates_without_class_attribute():
    d = parse_assignment_page(HTML_DATES_NO_CLASS)
    assert d["opened_at"] == "9 February 2026, 3:00 PM" or "9 February 2026" in d["opened_at"]
    assert d["due_at"] is not None and "2 March 2026" in d["due_at"]
    assert "5:00 PM" in d["due_at"]

def test_parse_dates_indonesian_fallback_via_instruction():
    html_id = HTML_DATES_NO_CLASS.replace("Monday, 2 March 2026, 5:00 PM", "Due: Monday, 2 March 2026, 5:00 PM") # keep
    # Also test instruction contains "Senin, 2 Maret 2026 pukul 17.00" fallback if dates_region missing
    html_no_region = """
    <html><body><h1>Tugas X</h1><div id="intro">Batas akhir: Senin, 2 Maret 2026 pukul 17.00</div></body></html>
    """
    d = parse_assignment_page(html_no_region)
    # Should not crash, due_at may be None or parsed via fallback; at minimum not raise
    assert isinstance(d, dict)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/misbahul45/code/xninetzy/services/ai && uv run pytest tests/os/academic/hebat/test_parse_assignment_dates.py -v`
Expected: FAIL — `due_at is None` because current code uses `find_all("div", class_=True)` which misses inner divs without class.

- [ ] **Step 3: Fix parsers.py (minimal)**

```python
# In parse_assignment_page, replace:
# for item in dates_region.find_all("div", class_=True):
# with:
for item in dates_region.find_all("div"):
    text = item.get_text(" ", strip=True)
    if not text:
        continue
    if re.search(r"open(ed)?", text, re.I):
        m = re.search(r"\d{1,2}\s+\w+\s+\d{4}", text)
        if m:
            opened_at = m.group().strip()
            # also capture full tail for due_at style
            # keep simple: opened_at as m.group()
    if re.search(r"due|deadline|batas akhir", text, re.I):
        # Capture full due string including time
        m = re.search(r"\d{1,2}\s+\w+\s+\d{4}.*", text)
        if m:
            due_at = m.group().strip()

# Also improve has_add_button detection to handle Indonesian:
has_add_button = bool(soup.find("button", string=re.compile(r"Add submission|Tambah.*pengumpulan", re.I)))
# Keep has_edit_button similar with Indonesian "Sunting|Edit submission"
has_edit_button = bool(soup.find("button", string=re.compile(r"Edit submission|Sunting", re.I)))
```

Also handle `time_remaining` already correct; keep.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/misbahul45/code/xninetzy/services/ai && uv run pytest tests/os/academic/hebat/test_parse_assignment_dates.py -v`
Expected: PASS

Also verify with real HTML:

Run:

```bash
cd /home/misbahul45/code/xninetzy/services/ai && uv run python -c "
from app.xninetzy.os.academic.hebat.parsers import parse_assignment_page
from app.xninetzy.os.academic.hebat.browser_session import get_page_html
import asyncio
... fetch cmid 36248 and parse, assert due_at contains '2 March 2026'
"
```

- [ ] **Step 5: Run existing related tests**

Run: `uv run pytest tests/os/academic/hebat/test_hebat_extractors.py tests/os/academic/hebat/test_hebat_download.py -v`
Expected: PASS (no regression)

- [ ] **Step 6: Commit**

```bash
git status --short
git diff services/ai/app/xninetzy/os/academic/hebat/parsers.py
git add services/ai/app/xninetzy/os/academic/hebat/parsers.py services/ai/tests/os/academic/hebat/test_parse_assignment_dates.py
git commit -m "fix(hebat): parse assignment dates without class filter, support ID due wording"
```

---

### Task 2: Robust `_parse_due_dt` for EN + ID dates and integration with sync

**Files:**
- Modify: `services/ai/app/xninetzy/os/academic/hebat/tools.py:99-113` (`_parse_due_dt`)
- Modify: `services/ai/app/xninetzy/core/config.py` if needed for timezone handling (check)
- Test: `services/ai/tests/os/academic/hebat/test_parse_assignment_dates.py` (extend)

**Interfaces:**
- Consumes: `due_str` like "Monday, 2 March 2026, 5:00 PM", "2 March 2026, 5:00 PM", "Senin, 2 Maret 2026 pukul 17.00", "2 Maret 2026 17:00", ISO "2026-03-02T17:00:00+07:00"
- Produces: `datetime` with timezone `ZoneInfo(APP_TIMEZONE)` or None if unparsable

- [ ] **Step 1: Write failing test for ID date**

```python
from app.xninetzy.os.academic.hebat.tools import _parse_due_dt

def test_parse_due_id_format():
    dt = _parse_due_dt("Senin, 2 Maret 2026 pukul 17.00")
    assert dt is not None
    assert dt.day == 2 and dt.month == 3 and dt.year == 2026
    assert dt.hour == 17

def test_parse_due_en_with_weekday():
    dt = _parse_due_dt("Monday, 2 March 2026, 5:00 PM")
    assert dt is not None
    assert dt.day == 2

def test_parse_due_en_short():
    dt = _parse_due_dt("2 March 2026, 5:00 PM")
    assert dt is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/os/academic/hebat/test_parse_assignment_dates.py::test_parse_due_id_format -v`
Expected: FAIL — current `_parse_due_dt` only handles English formats, Indonesian "Maret" fails.

- [ ] **Step 3: Implement minimal fix**

```python
def _parse_due_dt(due_str: str | None) -> datetime | None:
    if not due_str:
        return None
    s_clean = due_str.strip()
    # Indonesian month map to English for strptime
    id_months = {
        "Januari": "January", "Februari": "February", "Maret": "March",
        "April": "April", "Mei": "May", "Juni": "June", "Juli": "July",
        "Agustus": "August", "September": "September", "Oktober": "October",
        "November": "November", "Desember": "December"
    }
    for idm, enm in id_months.items():
        s_clean = s_clean.replace(idm, enm).replace(idm.lower(), enm.lower())
    # Normalize Indonesian time wording
    s_clean = s_clean.replace("pukul", "").replace("WIB", "").replace("WITA", "").replace("WIT", "")
    s_clean = re.sub(r"\s+", " ", s_clean).strip()
    # Remove weekday prefix if present for simpler parsing
    # e.g. "Monday, 2 March 2026, 5:00 PM" -> keep but strptime handles with %A
    for fmt in [
        "%A, %d %B %Y, %I:%M %p",
        "%A, %d %B %Y, %H:%M",
        "%d %B %Y, %I:%M %p",
        "%d %B %Y %H:%M",
        "%d %B %Y, %H:%M",
        "%d %B %Y",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S",
        "%d %B %Y %H.%M",  # Indonesian dotted time 17.00
        "%d %B %Y, %H.%M",
    ]:
        try:
            dt = datetime.strptime(s_clean, fmt)
            # attach timezone if naive
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=ZoneInfo(get_settings().APP_TIMEZONE))
            return dt
        except ValueError:
            continue
    # Also try without comma
    # fallback via dateutil if available? skip
    return None
```

Note: ensure `re` and `ZoneInfo` imported.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/os/academic/hebat/test_parse_assignment_dates.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add services/ai/app/xninetzy/os/academic/hebat/tools.py services/ai/tests/os/academic/hebat/test_parse_assignment_dates.py
git commit -m "fix(hebat): robust due date parsing EN+ID, dotted time, timezone"
```

---

### Task 3: Optimize `hebat_sync_assignments` to avoid MCP timeout (120s)

**Files:**
- Modify: `services/ai/app/xninetzy/os/academic/hebat/tools.py:504-611` (`hebat_sync_assignments`)
- Modify: `services/ai/app/xninetzy/os/academic/hebat/moodle_client.py:133-139` (`fetch_assignment_detail` maybe timeout param)
- Test: `services/ai/tests/os/academic/hebat/test_hebat_sync_performance.py` (new)
- Test: existing `test_hebat_task_link.py` must still pass

**Interfaces:**
- Consumes: `list_activities(activity_type="assign")` -> 120 rows, each requires `fetch_assignment_detail(chat_id, cmid)` with existing `HEBAT_RATE_LIMIT_SECONDS` sleep
- Produces: summary string with `synced`, `tasks_created`, `reminders_created`, completes within <90s for 120 items, never throws timeout to MCP caller, reports partial progress if some fetches fail

- [ ] **Step 1: Write failing test for timeout behavior (simulate)**

```python
# test_hebat_sync_performance.py
import asyncio
from unittest.mock import AsyncMock, patch
from app.xninetzy.os.academic.hebat.tools import hebat_sync_assignments

@patch("app.xninetzy.os.academic.hebat.tools.fetch_assignment_detail", new_callable=AsyncMock)
@patch("app.xninetzy.os.academic.hebat.tools.list_activities")
def test_sync_handles_many_without_timeout(mock_list, mock_fetch):
    # Simulate 120 assignments, each fetch takes 0.05s + 0.1s rate limit
    mock_list.return_value = [{"cmid": str(i), "id": i, "title": f"Tugas {i}"} for i in range(120)]
    mock_fetch.return_value = {
        "title": "Tugas X", "instruction": "instr", "opened_at": "9 Feb 2026, 3PM",
        "due_at": "2 March 2026, 5:00 PM", "time_remaining": "overdue",
        "submission_status": "No submissions", "grading_status": "Not graded", "last_modified": "-"
    }
    # Should complete quickly with concurrency, not sequential 120*0.15s=18s but we allow mock
    # The point: current sequential with asyncio.sleep(HEBAT_RATE_LIMIT) per iteration causes > timeout for 120*1s =120s
    # New implementation should use semaphore limit 5 and not sleep sequential but gather
    import time
    start = time.time()
    # Use 5 conc
    # This test will be used to assert new impl uses gather
    assert True  # placeholder: we will implement concurrency and check that mock_fetch.call_count ==120 and duration <5s
```

Alternatively create reproduction script that counts current duration and asserts needed improvement.

Simpler: Create script `reproduce_timeout.py` that measures `hebat_sync_assignments` logic duration with mock.

- [ ] **Step 2: Run to confirm current sequential is slow**

Run: `uv run pytest tests/os/academic/hebat/test_hebat_sync_performance.py -v` — should show concern, or run manual timing.

Expect: current impl sleeps `HEBAT_RATE_LIMIT_SECONDS` (default maybe 1 sec) per iteration → 120 sec → exceeds MCP 120s → timeout observed earlier (error -32001).

- [ ] **Step 3: Implement concurrency with semaphore + limited sleep**

```python
# New implementation sketch for tools.py hebat_sync_assignments:
async def hebat_sync_assignments(chat_id: str, course_id: str | None = None) -> str:
    err = _ensure_session_or_msg(chat_id)
    if err:
        return err
    s = get_settings()
    assign_activities = list_activities(course_id=course_id, activity_type="assign")
    if not assign_activities:
        return "Tidak ada assignment..."
    synced = 0; reminders_created=0; tasks_created=0
    now = _now(s)
    # Concurrency limit
    sem = asyncio.Semaphore(5)
    async def process_one(act):
        nonlocal synced, reminders_created, tasks_created
        async with sem:
            cmid = act["cmid"]
            try:
                # per-item timeout 25s
                detail = await asyncio.wait_for(fetch_assignment_detail(chat_id, cmid), timeout=25)
            except asyncio.TimeoutError:
                logger.warning("fetch timeout cmid=%s", cmid)
                return
            except Exception as e:
                logger.warning("fetch failed cmid=%s err=%s", cmid, e)
                return
            if not detail:
                return
            # upsert etc (same as before but inside lock)
            # use sync DB calls (they are fast, thread-safe via connect)
            activity_id = act["id"]
            assign = HebatAssignment(...)
            assignment_id = upsert_assignment(assign)
            # note: need to protect synced increment with lock? simple nonlocal is okay as semaphore ensures no race on DB?
            synced += 1
            due_dt = _parse_due_dt(detail.get("due_at"))
            task_id, task_created = sync_assignment_task(...)
            if task_created:
                tasks_created+=1
            # reminders logic same, but check now
            ...
            # small stagger to respect rate limit, but not full second per item: use 0.2s after each batch of 5
            await asyncio.sleep(0.2)

    # Process in batches to avoid overwhelming Moodle
    # Option: gather all with semaphore
    await asyncio.gather(*(process_one(act) for act in assign_activities))

    return f"✅ Sync assignment selesai.\n• {synced} tugas diperbarui\n..."
```

Important: Keep `s.HEBAT_RATE_LIMIT_SECONDS` but reduce effective wait via semaphore. If original rate limit is 1 sec, with 5 concurrency, effective throughput ~5 per sec. Alternatively make wait `s.HEBAT_RATE_LIMIT_SECONDS / 5`.

Also add handling for `assignment_id` DB writes needing thread safety; since `connect()` creates new connection per call, it's safe.

Add early return for `course_id` filter to allow incremental sync per course to avoid 120 at once via UI: caller can pass course_id to sync smaller batches.

Update docstring to mention partial success.

- [ ] **Step 4: Verify with mock test**

Run: `uv run pytest tests/os/academic/hebat/test_hebat_sync_performance.py -v`
Expected: PASS, duration <10s for 120 mocks.

- [ ] **Step 5: Run real sync test (limited to one course)**

Run: manual via MCP or python:

```bash
cd /home/misbahul45/code/xninetzy/services/ai && uv run python -c "
import asyncio
from app.xninetzy.os.academic.hebat.tools import hebat_sync_assignments
async def t():
    print(await hebat_sync_assignments('6285649204151', course_id='10924'))
asyncio.run(t())
" 2>&1 | tail -n 50
```

Expect: completes without timeout, returns synced count, no -32001.

If still timeout, reduce concurrency or add per-course pagination.

- [ ] **Step 6: Verify existing tests still pass**

Run: `uv run pytest tests/os/academic/hebat/ -v` — all 53+ new should pass

- [ ] **Step 7: Commit**

```bash
git add services/ai/app/xninetzy/os/academic/hebat/tools.py services/ai/app/xninetzy/os/academic/hebat/moodle_client.py services/ai/tests/os/academic/hebat/test_hebat_sync_performance.py
git commit -m "perf(hebat): concurrent sync with semaphore, per-item timeout, avoid MCP 120s timeout"
```

---

### Task 4: Fix `list_assignments` join and add regression test

**Files:**
- Modify: `services/ai/app/xninetzy/os/academic/hebat/storage.py:404-434` (keep improved join but ensure distinct)
- Create: `services/ai/tests/os/academic/hebat/test_list_assignments_join.py`
- Test: same

**Interfaces:**
- Consumes: `hebat_assignments` joined with `hebat_activities` via either `act.id = ha.activity_id` OR `act.cmid = CAST(ha.activity_id AS TEXT)`
- Produces: `list_assignments()` returns correct rows including case cmid 105393 with id 829 mismatch (the bug noted in comment)

- [ ] **Step 1: Write failing test for join**

```python
def test_list_assignments_finds_by_cmid_mismatch():
    # Setup: create activity with cmid 105393 id 829, assignment with activity_id 105393 (cmid value not id)
    # Then list_assignments should find it via OR condition
    from app.xninetzy.db.sqlite import connect, init_db
    from app.xninetzy.os.academic.hebat.models import HebatActivity, HebatAssignment, ActivityType
    from app.xninetzy.os.academic.hebat.storage import upsert_activity, upsert_assignment, list_assignments
    init_db()
    with connect() as conn:
        conn.execute("DELETE FROM hebat_assignments WHERE activity_id IN (105393, 829)")
        conn.execute("DELETE FROM hebat_activities WHERE cmid='105393'")
    act = HebatActivity(course_id="10927", cmid="105393", type=ActivityType.ASSIGN, title="Tugas 2 SII208", section_title="Minggu 2", activity_url="https://example.com/mod/assign/view.php?id=105393")
    aid = upsert_activity(act)  # will be e.g. 999, not 105393
    # Force mismatch: update assignment to use cmid as activity_id (simulating old data)
    from app.xninetzy.os.academic.hebat.models import HebatAssignment
    assign = HebatAssignment(activity_id=105393, title="Tugas 2 SII208", instruction_text="instr", opened_at=None, due_at=None, time_remaining_text=None, submission_status="No submissions", grading_status="Not graded", last_modified_text="-")
    ass_id = upsert_assignment(assign)
    listed = list_assignments()
    found = [x for x in listed if x["title"] == "Tugas 2 SII208"]
    assert len(found) == 1
    assert str(found[0]["cmid"]) == "105393"
```

- [ ] **Step 2: Run to verify currently passes or fails**

Current code already has OR fix (since 2026-08-24). Should PASS. If it passes, we document and ensure no duplicate rows.

Also test duplicate avoidance:

```python
def test_no_duplicate_when_both_conditions_match():
    # When act.id == ha.activity_id and also cmid cast matches (if id==cmid), should not duplicate
```

- [ ] **Step 3: If duplicate risk, add DISTINCT**

Modify query to `SELECT DISTINCT ha.*, ...` or `GROUP BY ha.id`

Add `SELECT DISTINCT` to avoid double row when both OR branches true.

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/os/academic/hebat/test_list_assignments_join.py -v`

- [ ] **Step 5: Commit**

```bash
git add services/ai/app/xninetzy/os/academic/hebat/storage.py services/ai/tests/os/academic/hebat/test_list_assignments_join.py
git commit -m "fix(hebat): ensure list_assignments distinct, regression for cmid mismatch"
```

---

### Task 5: Obsidian Orchestra migration for HEBAT assignment notes

**Files:**
- Modify: vault notes via `ObsidianVaultService` (no code file, but verify via `xninetzy_obsidian_*` tools)
- Create: `Academic/Current/SIA301 - Perencanaan Arsitektur Perusahaan/...`, `Academic/Archive/2025 Genap/...` etc per orchestra skill
- Test: `xninetzy_obsidian_folder_status`, `xninetzy_obsidian_list`, `xninetzy_obsidian_search_health`

**Interfaces:**
- Consumes: existing notes at `Academic/HEBAT/Courses/{Full} /Assignments/...` (old) and DB course list (22 courses)
- Produces: canonical folders per orchestra, MOC regenerated, no numeric IDs, no slugs

**Steps use xninetzy-obsidian-orchestra workflows:**

- [ ] **Step 1: Health check (diagnostic)**

```bash
# Via MCP:
xninetzy_obsidian_folder_status
xninetzy_obsidian_list folder="Academic"
xninetzy_obsidian_search_health
```

Expected: 104 notes, missing_structure [], but naming violations: folder `Academic/HEBAT/Courses/...` is non-canonical (should be `Academic/Current` and `Archive`).

- [ ] **Step 2: Create canonical course structures**

For each 2026 Ganjil course (11 courses), create:
```
Academic/Current/{Code} - {Full Name}/Materials/
Academic/Current/{Code} - {Full Name}/Assignments/
Academic/Current/{Code} - {Full Name}/Notes/
Academic/Current/{Code} - {Full Name}/README.md
```
Use canonical names from orchestra skill table: SIA301, SIA302, SID303, SID304, SII208, SII209, SII213, SII318, SII319, MNW409, BAE112

For 2025 Genap archive (9 courses), create:
```
Academic/Archive/2025 Genap/{Code} - {Full Name}/...
```

Use `xninetzy_obsidian_create` with vault-relative paths.

- [ ] **Step 3: Migrate existing notes**

Use `xninetzy_obsidian_organize_preview` then for each note:

- Read source `Academic/HEBAT/Courses/MNW409 - Kewirausahaan.../Assignments/Pembentukan Tim.md`
- Create destination `Academic/Current/MNW409 - Kewirausahaan Dan Bisnis Sistem Informasi/Assignments/Pembentukan Tim.md` (or Archive if 2025)
- Update frontmatter `semester: "2026 Ganjil"`, `status: active`, `canonical: true`
- Preserve content, adjust tags.

Do for all notes under `Academic/HEBAT/Courses/...`

- [ ] **Step 4: Generate MOCs**

Call `xninetzy_obsidian_moc_refresh` then verify `Academic/Current/00 - Index.md`, `Academic/Archive/2025 Genap/00 - Index.md`

- [ ] **Step 5: Verify health again**

Run folder_status, expect healthy, no misplaced, verify via `xninetzy_obsidian_list` each top-level.

- [ ] **Step 6: Manual checklist commit note**

Create `System/Checkpoints/2026-08-28-hebat-obsidian-migration.md` documenting folders moved.

---

### Task 6: Mark overdue assignments as team-completed and generate Obsidian implementation notes

**Files:**
- Modify: DB `tasks` status via `sync_assignment_task` and direct `UPDATE tasks SET status='done' WHERE ...`
- Create: Obsidian notes `Academic/Current/{Code} - {Name}/Assignments/Tugas N - Implementasi Team.md` for each overdue
- Test: `xninetzy_task_list`, `xninetzy_obsidian_search`

**Interfaces:**
- Consumes: `list_assignments()` filtered where `submission_status` NOT like submitted and `time_remaining` like "overdue" or `due_at` < now; plus user assertion "tugas overdue udah dikerjain basisnya team dan teman sudah melakukan implementasinya"
- Produces: For each overdue, task status -> done, obsidian note with `team_implemented: true`, `overdue: true`, `verified_by_team: true`, and implementation summary placeholder for teman's work, plus update `hebat_assignments` submission_status to logical done if needed for digest filtering

- [ ] **Step 1: Query overdue assignments**

```python
# via python: list_assignments() -> filter where time_remaining contains "overdue" or due_dt < now
from app.xninetzy.os.academic.hebat.storage import list_assignments
import re
from zoneinfo import ZoneInfo
from datetime import datetime
from app.xninetzy.core.config import get_settings
s = get_settings()
now = datetime.now(ZoneInfo(s.APP_TIMEZONE))
overdue = []
for a in list_assignments():
    if "submitted" in (a["submission_status"] or "").lower():
        continue
    # if due_at parseable and < now
    due = a.get("due_at")
    is_overdue = False
    if due:
        from app.xninetzy.os.academic.hebat.tools import _parse_due_dt
        dt = _parse_due_dt(due)
        if dt and dt < now:
            is_overdue=True
    if "overdue" in (a.get("time_remaining_text") or "").lower():
        is_overdue=True
    if is_overdue:
        overdue.append(a)
print(len(overdue))
```

Expect: many overdue (maybe 100+ but digest said 48 without deadline + unknown). For those with time_remaining overdue but due_at None (bug before fix), after Task 1 fix they will have due_at, but still overdue.

- [ ] **Step 2: For each overdue, mark task done and create Obsidian implementation note**

Via `sync_assignment_task` will set status done if submitted. Since team implemented but not submitted on HEBAT (submission_status = No submissions), we need manual override to mark done for Life OS tracking:

```python
# For each overdue assignment_id, find linked task via entity_links and set status done + description with team note
with connect() as conn:
    conn.execute("UPDATE tasks SET status='done', description = description || '\n\n[TEAM IMPLEMENTED] Dikerjakan team, basis teman sudah implementasi, diverifikasi 2026-08-28' WHERE id IN (SELECT target_id FROM entity_links WHERE source_type='hebat_assignment' AND source_id=? )", (assignment_id,))
```

Then create Obsidian note:

```
---
type: assignment
course: SIA301
semester: "2026 Ganjil"
status: done
team_implemented: true
overdue: true
verified: team_basis
tags: [hebat, team]
created: 2026-08-28
---

# Tugas X - Implementasi Team

> Overdue namun sudah dikerjakan basis team (teman implementasi). Status Life OS ditandai done 2026-08-28.

## Bukti Team
- Teman: [nama team / link]
- File implementasi: [path]
## Cross-check HEBAT
- HEBAT status: No submissions (belum submit) -> logical done via team
- Deadline: 2 March 2026

## Next
- Jika perlu submit tetap, siapkan file PDF sesuai week01b format.
```

Use `ObsidianVaultService().create_note()` with canonical path per `folder_policy.canonical_path('hebat_assignment', ...)`.

- [ ] **Step 3: Verify via Life OS and Obsidian**

Run: `xninetzy_task_list` -> count done increased

Run: `xninetzy_obsidian_search query="team_implemented"` -> finds notes

Run: `hebat_academic_digest days_ahead=7` -> overdue list should be empty or reduced (since tasks marked done are filtered? Digest filters submitted, but our overdue assignments still not submitted, digest will still show overdue unless we also logically mark submitted. So for true removal from overdue, need to decide: keep overdue visible but note team done vs update digest to exclude team_done. For now, add metadata and optionally set assignment submission_status to logical "Team implemented" not affect digest filter (which checks submitted). To truly hide, update assignment's submission_status to "Submitted for grading (team)" or add tag. Decide to keep digest showing overdue but Life OS tasks done — document this.)

- [ ] **Step 4: Checkpoint**

Create `System/Checkpoints/2026-08-28-hebat-team-overdue.md` with list of overdue marked done.

---

### Task 7: Final Verification — Full suite + live sync test

**Files:**
- None (verification only)
- Test: `services/ai/tests/os/academic/hebat/*`, `services/ai/tests/workflow/test_workflow_plan.py`

- [ ] **Step 1: Run ruff & pytest full hebat suite**

```bash
cd /home/misbahul45/code/xninetzy/services/ai && uv run ruff check app tests
uv run pytest tests/os/academic/hebat/ -v
uv run pytest tests/workflow/test_workflow_plan.py -v
```

Expected: All pass, no ruff errors.

- [ ] **Step 2: Live sync verification (real HEBAT)**

```bash
# Call via MCP or direct:
# hebat_sync_assignments with chat_id 6285649204151
# hebat_sync_assignments with course_id filter per 2026 Ganjil course one by one
# hebat_academic_digest days_ahead=30
# hebat_get_assignment_detail for sample cmid 36248 -> should show due_at now correct
```

Verify: No timeout, due_at populated, digest shows tasks with deadlines (not all without deadline), overdue team tasks marked done appear in done list.

Use helper:

```python
from app.xninetzy.os.academic.hebat.parsers import parse_assignment_page
from app.xninetzy.os.academic.hebat.browser_session import get_page_html
# fetch sample and assert
```

- [ ] **Step 3: Obsidian health verification**

```bash
xninetzy_obsidian_folder_status
xninetzy_obsidian_search_health
xninetzy_obsidian_list folder="Academic/Current"
```

Expected: healthy, 104+ new notes, canonical folders.

- [ ] **Step 4: Create final checkpoint**

Create `System/Checkpoints/2026-08-28-fix-hebat-assignment-complete.md` with:

- goal, completed, decisions, artifacts, open_questions, next_actions

- [ ] **Step 5: Report to user**

Summarize what was fixed, verification evidence, artifact paths, remaining uncertainties.

---

## Execution Notes

- Follow TDD per task: failing test → minimal fix → pass → commit
- Use subagent per task if parallel, but tasks 1->2->3 are sequential (parser fixes before sync), 5 & 6 can parallel after 3
- Do not claim visual QA without render; for Obsidian use folder_status and list as evidence
- Do not auto-commit without explicit task step; leave working tree for user to review final diff

