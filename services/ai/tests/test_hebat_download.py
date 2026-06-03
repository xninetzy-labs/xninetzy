"""Offline unit tests for the HEBAT download/resolve/analyze slice."""

from __future__ import annotations

from app.tools.hebat.assignment_extractor import extract_assignment_detail_from_html
from app.tools.hebat.content_analyzer import analyze_downloaded_file
from app.tools.hebat.download_resolver import extract_download_candidates
from app.tools.hebat.moodle_client import _is_login_html_bytes
from app.tools.hebat.resource_extractor import extract_resource_detail_from_html
from app.tools.hebat import storage

BASE = "https://hebat.elearning.unair.ac.id"

ASSIGN_HTML = """
<html><body>
<h1>Tugas 1 - Esai</h1>
<div data-region="activity-dates"><div>Due: 30 June 2026</div></div>
<div id="intro">
  Kerjakan esai 1000 kata.
  <a href="/pluginfile.php/1/mod_assign/intro/soal.pdf">soal.pdf</a>
</div>
<table class="submissionstatustable generaltable">
  <tr><th>Submission status</th><td>Submitted for grading</td></tr>
  <tr><th>Grading status</th><td>Not graded</td></tr>
  <div class="assignsubmission_file">
    <a href="/pluginfile.php/2/assignsubmission_file/sf/jawaban.pdf">jawaban.pdf</a>
  </div>
</table>
<div class="feedback feedbacktable">
  <a href="/pluginfile.php/3/assignfeedback_file/ff/koreksi.pdf">koreksi.pdf</a>
</div>
</body></html>
"""

RESOURCE_HTML = """
<html><body>
<h1>Slide Minggu 1</h1>
<div id="intro">Deskripsi slide pengantar</div>
<div class="resourcecontent">
  <a href="/pluginfile.php/9/mod_resource/content/1/slide.pdf">slide.pdf</a>
</div>
</body></html>
"""


def test_extract_download_candidates_tags_source():
    cands = extract_download_candidates(RESOURCE_HTML, BASE, source="resource")
    assert len(cands) == 1
    assert cands[0].source == "resource"
    assert cands[0].filename == "slide.pdf"
    assert cands[0].url.startswith(BASE)


def test_assignment_detail_classifies_files():
    detail = extract_assignment_detail_from_html(ASSIGN_HTML, BASE)
    assert detail["title"] == "Tugas 1 - Esai"
    assert detail["submission_status"] == "Submitted for grading"
    attach = [a["filename"] for a in detail["attachments"]]
    feedback = [a["filename"] for a in detail["feedback_files"]]
    submission = [a["filename"] for a in detail["submission_files"]]
    assert "soal.pdf" in attach
    assert "koreksi.pdf" in feedback
    assert "jawaban.pdf" in submission
    assert "Kerjakan esai" in detail["raw_clean_text"]


def test_resource_detail_extracts_files_and_title():
    detail = extract_resource_detail_from_html(RESOURCE_HTML, BASE)
    assert detail["title"] == "Slide Minggu 1"
    assert "Deskripsi slide" in (detail["description"] or "")
    assert detail["file_count"] == 1
    assert detail["files"][0]["filename"] == "slide.pdf"


def test_is_login_html_bytes_guard():
    login = b'<html><form><input name="logintoken" value="x"><input name="password"></form></html>'
    assert _is_login_html_bytes("text/html; charset=utf-8", login)
    # A real PDF is never a login page.
    assert not _is_login_html_bytes("application/pdf", b"%PDF-1.7 ...")
    # Genuine HTML content is not the login form.
    assert not _is_login_html_bytes("text/html", b"<html><body><h1>Materi</h1></body></html>")


def test_analyze_txt_and_html(tmp_path):
    txt = tmp_path / "note.txt"
    txt.write_text("Konsep graph rag dan retrieval augmented generation", encoding="utf-8")
    out = analyze_downloaded_file(str(txt))
    assert out["supported"] and out["error"] is None
    assert out["word_count"] > 0
    assert "graph rag" in out["summary"].lower()

    html = tmp_path / "page.html"
    html.write_text("<html><body><script>x</script><h1>Judul</h1><p>Isi materi</p></body></html>",
                    encoding="utf-8")
    out_html = analyze_downloaded_file(str(html))
    assert out_html["kind"] == "html"
    assert "Isi materi" in out_html["text"]
    assert "x" not in out_html["text"]  # script stripped


def test_analyze_missing_file():
    out = analyze_downloaded_file("/nope/does-not-exist.pdf")
    assert out["supported"] is False
    assert out["error"]


def test_record_and_search_downloads():
    chat = "test-dl-628"
    storage.record_download(
        chat, file_url=f"{BASE}/pluginfile.php/1/x/graphrag-paper.pdf",
        cmid="555", filename="graphrag-paper.pdf",
        text_excerpt="graph rag retrieval augmented generation intro",
        summary="paper tentang graph rag",
    )
    found = storage.search_downloads(chat, query="graph rag")
    assert any(d["filename"] == "graphrag-paper.pdf" for d in found)
    all_for_chat = storage.search_downloads(chat)
    assert len(all_for_chat) >= 1
