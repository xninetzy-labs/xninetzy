"""Regression for HEBAT assignment date parsing — root cause: class_=True misses inner divs."""

from xninetzy.os.academic.hebat.parsers import parse_assignment_page

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

REAL_HTML_SNIPPET = """
<div class="activity-dates" data-region="activity-dates">
 <div>
  <strong>
   Opened:
  </strong>
  Monday, 9 February 2026, 3:00 PM
 </div>
 <div>
  <strong>
   Due:
  </strong>
  Monday, 2 March 2026, 5:00 PM
 </div>
</div>
"""


def test_parse_dates_without_class_attribute():
    d = parse_assignment_page(HTML_DATES_NO_CLASS)
    assert d["opened_at"] is not None, "opened_at should not be None"
    assert "9 February 2026" in d["opened_at"], f"got {d['opened_at']}"
    assert d["due_at"] is not None, "due_at should not be None — bug class_=True"
    assert "2 March 2026" in d["due_at"], f"got {d['due_at']}"
    assert "5:00 PM" in d["due_at"]


def test_parse_dates_indonesian_fallback_via_instruction():
    html_no_region = """
    <html><body><h1>Tugas X</h1><div id="intro">Batas akhir: Senin, 2 Maret 2026 pukul 17.00</div></body></html>
    """
    d = parse_assignment_page(html_no_region)
    assert isinstance(d, dict)
    # Should not crash; due_at may be None (no dates_region) — at minimum dict
    assert "title" in d


def test_parse_due_dari_real_hebat_structure():
    # Minimal real snippet with whitespace and strong tags
    html = f"<html><body><h1>Test</h1>{REAL_HTML_SNIPPET}<div id='intro'>x</div></body></html>"
    d = parse_assignment_page(html)
    assert d["due_at"] and "2 March 2026" in d["due_at"]
    assert d["opened_at"] and "9 February 2026" in d["opened_at"]


def test_parse_due_id_format():
    from xninetzy.os.academic.hebat.tools import _parse_due_dt

    dt = _parse_due_dt("Senin, 2 Maret 2026 pukul 17.00")
    assert dt is not None, "ID date should parse"
    assert dt.day == 2 and dt.month == 3 and dt.year == 2026
    assert dt.hour == 17

    dt2 = _parse_due_dt("2 Maret 2026 17:00")
    assert dt2 is not None
    assert dt2.day == 2


def test_parse_due_en_with_weekday():
    from xninetzy.os.academic.hebat.tools import _parse_due_dt

    dt = _parse_due_dt("Monday, 2 March 2026, 5:00 PM")
    assert dt is not None
    assert dt.day == 2
    assert dt.month == 3

    dt2 = _parse_due_dt("2 March 2026, 5:00 PM")
    assert dt2 is not None
    assert dt2.day == 2


def test_parse_due_en_short():
    from xninetzy.os.academic.hebat.tools import _parse_due_dt

    dt = _parse_due_dt("2 March 2026")
    assert dt is not None
    assert dt.day == 2
