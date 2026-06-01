"""Manual end-to-end HEBAT/Moodle integration check.

This is NOT collected by pytest (filename does not start with ``test_``) because
it requires real HEBAT credentials and live network access to UNAIR Moodle.

It verifies the full real path: login -> session check -> fetch courses ->
fetch course activities -> download a material file.

Run from the repo root (so the root ``.env`` with HEBAT_USERNAME/PASSWORD loads),
pointing the data dirs at a writable location:

    PYTHONPATH=services/ai \
      SQLITE_PATH=/tmp/hebat_test.sqlite3 \
      DATA_DIR=/tmp/hebat_data \
      HEBAT_DATA_DIR=/tmp/hebat_data_fresh \
      HEBAT_DOWNLOAD_DIR=/tmp/hebat_dl \
      uv run --project services/ai python services/ai/tests/manual_hebat_e2e.py

Output is masked: cookies/tokens/sesskey are never printed.

Verified working 2026-06-02: login OK, 10 courses, 20 activities,
downloaded a 251 KB application/pdf.
"""
from __future__ import annotations

import asyncio
import os
from pathlib import Path

from app.core.config import get_settings
from app.db.migrations import run_migrations
from app.db.sqlite import init_db

CHAT_ID = os.getenv("HEBAT_TEST_CHAT_ID", "6285649204151@s.whatsapp.net")


async def main() -> int:
    init_db()
    run_migrations()
    s = get_settings()
    print(f"[env] username_read={bool(s.HEBAT_USERNAME)} password_read={bool(s.HEBAT_PASSWORD)}")
    print(f"[env] base={s.HEBAT_BASE_URL}")

    from app.tools.hebat.browser_session import check_session_valid, login_with_credentials
    from app.tools.hebat.models import HebatActivity, HebatCourse
    from app.tools.hebat.moodle_client import (
        download_file,
        fetch_course_activities,
        fetch_courses,
    )
    from app.tools.hebat.storage import upsert_activity, upsert_course

    # 1. reuse stored session if still valid
    valid, name = await check_session_valid(CHAT_ID)
    print(f"[1] session_valid={valid} profile={name!r}")

    # 2. fall back to credential login
    if not valid:
        print("[2] logging in with credentials...")
        ok = await login_with_credentials(CHAT_ID, s.HEBAT_USERNAME, s.HEBAT_PASSWORD)
        print(f"[2] login_success={ok}")
        if not ok:
            print("FAIL: login failed")
            return 1

    # 3. fetch courses (JS-rendered page -> Playwright path)
    courses = await fetch_courses(CHAT_ID)
    print(f"[3] courses_fetched={len(courses)}")
    for c in courses[:8]:
        print(f"    - {c['fullname'][:60]} (id={c['moodle_course_id']})")
        upsert_course(HebatCourse(**c))
    if not courses:
        print("FAIL: no courses returned")
        return 1

    # 4. activities for first course
    cid = courses[0]["moodle_course_id"]
    acts = await fetch_course_activities(CHAT_ID, cid)
    by_type: dict[str, int] = {}
    for a in acts:
        t = a["type"].value if hasattr(a["type"], "value") else str(a["type"])
        by_type[t] = by_type.get(t, 0) + 1
        upsert_activity(
            HebatActivity(
                course_id=cid,
                cmid=a["cmid"],
                type=a["type"],
                title=a["title"],
                section_title=a.get("section_title"),
                activity_url=a["activity_url"],
            )
        )
    print(f"[4] activities in course {cid}: {len(acts)} types={by_type}")
    if not acts:
        print("FAIL: no activities returned")
        return 1

    # 5. download a material file
    res = [
        a
        for a in acts
        if (a["type"].value if hasattr(a["type"], "value") else str(a["type"])) == "resource"
    ]
    if not res:
        print("[5] no resource activity to download (course has none); skipping download")
        return 0
    target = res[0]
    dest = Path(s.HEBAT_DOWNLOAD_DIR) / f"{target['cmid']}.bin"
    meta = await download_file(CHAT_ID, target["activity_url"], dest)
    if not meta:
        print("FAIL: download returned None")
        return 1
    print(
        f"[5] DOWNLOAD OK file={meta['filename']!r} "
        f"size={meta['size_bytes']}B mime={meta['mime_type']} sha={meta['sha256'][:12]}..."
    )
    print("PASS: HEBAT login + get data + download all working")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
