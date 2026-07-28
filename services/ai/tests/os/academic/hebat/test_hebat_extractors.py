"""Offline unit tests for the HEBAT HTML extractor slice.

Uses representative Moodle-shaped HTML — no network / browser / live account.
"""

from __future__ import annotations

from app.xninetzy.os.academic.hebat.course_extractor import (
    extract_course_outline_from_html,
    extract_courses_from_html,
)
from app.xninetzy.os.academic.hebat.html_cleaner import clean_moodle_html, html_to_readable_text
from app.xninetzy.os.academic.hebat.link_extractor import (
    extract_file_links,
    extract_mod_links,
    looks_like_file_url,
)
from app.xninetzy.os.academic.hebat.models import ActivityType

BASE = "https://hebat.elearning.unair.ac.id"

DASHBOARD = """
<html><body>
<nav class="navbar">menu junk</nav>
<div class="course-content">
  <div class="dashboard-card">
    <a href="/course/view.php?id=101" class="coursename">Kecerdasan Buatan</a>
  </div>
  <div class="dashboard-card">
    <a href="/course/view.php?id=102">Basis Data Lanjut</a>
  </div>
  <a href="/course/view.php?id=101">Kecerdasan Buatan (dup)</a>
</div>
<footer id="page-footer">copyright junk</footer>
<script>var x = 1;</script>
</body></html>
"""

COURSE = """
<html><body>
<header><h1>Kecerdasan Buatan</h1></header>
<div class="course-content"><ul class="topics">
  <li class="section main" id="section-1">
   <div class="content">
    <h3 class="sectionname">Minggu 1 - Pengantar</h3>
    <div class="summary">Pengenalan AI dan sejarahnya</div>
    <ul class="section img-text">
      <li class="activity assign modtype_assign" data-for="cmitem" id="module-37302">
        <a href="/mod/assign/view.php?id=37302" class="aalink">
          <span class="instancename">Tugas 1 - Esai<span class="accesshide"> Assignment</span></span>
        </a>
        <div class="activityinstance">Due: 30 June 2026, 23:59</div>
      </li>
      <li class="activity resource modtype_resource" data-for="cmitem" id="module-37310">
        <a href="/mod/resource/view.php?id=37310" class="aalink">
          <span class="instancename">Slide Pengantar<span class="accesshide"> File</span></span>
        </a>
      </li>
    </ul>
   </div>
  </li>
  <li class="section main" id="section-2">
   <div class="content">
    <h3 class="sectionname">Minggu 2 - Search</h3>
    <ul class="section img-text">
      <li class="activity forum modtype_forum" data-for="cmitem" id="module-37320">
        <a href="/mod/forum/view.php?id=37320" class="aalink">
          <span class="instancename">Diskusi Search<span class="accesshide"> Forum</span></span>
        </a>
        <div class="availabilityinfo">Not available unless: you belong to Group A</div>
      </li>
    </ul>
   </div>
  </li>
</ul></div>
</body></html>
"""

RESOURCE_PAGE = """
<html><body>
<div class="resourcecontent">
  <a href="https://hebat.elearning.unair.ac.id/pluginfile.php/123/mod_resource/content/1/slide.pdf">slide.pdf</a>
  <a href="/mod/resource/view.php?id=999?forcedownload=1">download</a>
  <a href="/course/view.php?id=101">back to course</a>
</div>
</body></html>
"""


# ─── html_cleaner ────────────────────────────────────────────────────────────

def test_clean_removes_chrome_keeps_content():
    cleaned = clean_moodle_html(DASHBOARD)
    assert "menu junk" not in cleaned
    assert "copyright junk" not in cleaned
    assert "var x" not in cleaned
    assert "Kecerdasan Buatan" in cleaned


def test_readable_text_inlines_links():
    text = html_to_readable_text(RESOURCE_PAGE)
    assert "slide.pdf" in text
    assert "pluginfile.php" in text  # href survived flattening


# ─── link_extractor ──────────────────────────────────────────────────────────

def test_looks_like_file_url():
    assert looks_like_file_url(f"{BASE}/pluginfile.php/1/mod_resource/content/x.pdf")
    assert looks_like_file_url("/mod/resource/view.php?id=1&forcedownload=1")
    assert looks_like_file_url("/files/a.docx")
    assert not looks_like_file_url("/mod/assign/view.php?id=1")
    assert not looks_like_file_url("")


def test_extract_mod_links_dedupes_and_types():
    links = extract_mod_links(COURSE, BASE)
    cmids = {l["cmid"]: l["type"] for l in links}
    assert cmids["37302"] == ActivityType.ASSIGN
    assert cmids["37310"] == ActivityType.RESOURCE
    assert cmids["37320"] == ActivityType.FORUM
    assert links[0]["activity_url"].startswith(BASE)


def test_extract_file_links_finds_pluginfile():
    files = extract_file_links(RESOURCE_PAGE, BASE)
    urls = [f["url"] for f in files]
    assert any("pluginfile.php" in u for u in urls)
    assert any(f["filename"] == "slide.pdf" for f in files)
    # The /course/view link is NOT a file.
    assert not any("course/view.php" in u for u in urls)


# ─── course_extractor ────────────────────────────────────────────────────────

def test_extract_courses_dedupes():
    courses = extract_courses_from_html(DASHBOARD, BASE)
    ids = {c["moodle_course_id"] for c in courses}
    assert ids == {"101", "102"}
    ku = next(c for c in courses if c["moodle_course_id"] == "101")
    assert ku["course_url"] == f"{BASE}/course/view.php?id=101"


def test_extract_course_outline_structure():
    outline = extract_course_outline_from_html(COURSE, BASE, course_id="101")
    assert outline.title == "Kecerdasan Buatan"
    assert len(outline.sections) == 2
    s1 = outline.sections[0]
    assert s1.title == "Minggu 1 - Pengantar"
    assert "Pengenalan AI" in (s1.summary or "")
    assert outline.activity_count == 3

    assign = next(a for s in outline.sections for a in s.activities if a.cmid == "37302")
    assert assign.type == ActivityType.ASSIGN
    assert assign.title == "Tugas 1 - Esai"  # accesshide suffix stripped
    assert assign.due_date_text and "Due" in assign.due_date_text

    forum = next(a for s in outline.sections for a in s.activities if a.cmid == "37320")
    assert forum.availability_text and "Group A" in forum.availability_text

    counts = outline.counts_by_type()
    assert counts.get("assign") == 1 and counts.get("resource") == 1 and counts.get("forum") == 1


def test_outline_fallback_flat_when_no_sections():
    flat_html = """
    <html><body>
      <a href="/mod/quiz/view.php?id=500">Kuis 1</a>
      <a href="/mod/url/view.php?id=501">Link Materi</a>
    </body></html>
    """
    outline = extract_course_outline_from_html(flat_html, BASE, course_id="77")
    assert len(outline.sections) == 1
    assert outline.sections[0].title == "General"
    assert outline.activity_count == 2
