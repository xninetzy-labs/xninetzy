from __future__ import annotations

import json
from pathlib import Path

import pytest

from xninetzy.integrations.document_studio import markup, themes
from xninetzy.integrations.document_studio.convert import office_binary
from xninetzy.integrations.document_studio.docx_render import render_docx
from xninetzy.integrations.document_studio.errors import DocumentStudioError
from xninetzy.integrations.document_studio.pptx_render import render_pptx
from xninetzy.integrations.document_studio.studio import _heading_pages
from xninetzy.integrations.document_studio.theme_extract import contrast, extract_theme

docx = pytest.importorskip("docx")
pptx = pytest.importorskip("pptx")

SAMPLE = """---
title: Laporan Uji
author: [A, B]
student_id: [1, 2]
course: RPL
---

# Pendahuluan

Teks **tebal**, *miring* dan [tautan](https://example.org).

- satu
  - dua
1. pertama
2. kedua

Notes: catatan pembicara

# Data

Tabel: Ringkasan

| Nama | Nilai |
|---|---:|
| a | 1 |
| b | 2 |
"""


def test_front_matter_and_inline_runs():
    meta, body = markup.split_front_matter(SAMPLE)
    assert meta["title"] == "Laporan Uji" and meta["author"] == ["A", "B"]
    blocks = markup.parse_blocks(body)
    paragraph = next(b for b in blocks if b.kind == "paragraph")
    kinds = [(r.text, r.bold, r.italic, r.link) for r in paragraph.runs]
    assert ("tebal", True, False, "") in kinds
    assert ("miring", False, True, "") in kinds
    assert ("tautan", False, False, "https://example.org") in kinds


def test_lists_tables_and_captions_parse():
    _, body = markup.split_front_matter(SAMPLE)
    blocks = markup.parse_blocks(body)
    items = next(b for b in blocks if b.kind == "list").items
    assert [(level, ordered) for level, ordered, _ in items] == [(0, False), (1, False), (0, True), (0, True)]
    table = next(b for b in blocks if b.kind == "table")
    assert table.caption == "Ringkasan"
    assert table.align == ["left", "right"]
    assert len(table.rows) == 2


def test_slides_split_on_headings_and_capture_notes():
    _, body = markup.split_front_matter(SAMPLE)
    slides = markup.to_slides(markup.parse_blocks(body))
    assert [s.title for s in slides] == ["Pendahuluan", "Data"]
    assert slides[0].notes == "catatan pembicara"
    explicit = markup.to_slides(markup.parse_blocks("# A\n\nx\n\n---\n\n# B\n\ny\n"))
    assert [s.title for s in explicit] == ["A", "B"]


def test_invalid_front_matter_is_rejected():
    with pytest.raises(DocumentStudioError):
        markup.split_front_matter("---\n- not\n- a mapping\n---\nbody")


def test_builtin_academic_theme_matches_hebat_standard():
    theme = themes.load_theme("academic-hebat")
    assert theme.fonts.body == "Times New Roman"
    assert (theme.sizes.body, theme.sizes.h1, theme.sizes.h2, theme.sizes.h3) == (12, 24, 16, 13)
    assert theme.document.line_spacing == 1.5
    assert (theme.page.margin_top_cm, theme.page.margin_left_cm) == (2.3, 2.5)
    assert {t["name"] for t in themes.list_themes()} >= {"academic-hebat", "professional", "minimal", "consulting"}


def test_save_theme_is_owner_scoped_and_protects_builtins():
    theme, path = themes.save_theme("my-brand", {"colors": {"accent": "#c0392b"}}, base="minimal")
    assert path.parent == themes.user_theme_dir()
    assert theme.colors.accent == "#C0392B"
    assert themes.load_theme("my-brand").colors.accent == "#C0392B"
    with pytest.raises(DocumentStudioError):
        themes.save_theme("professional", {})
    with pytest.raises(ValueError):
        themes.save_theme("bad-color", {"colors": {"accent": "red"}})


def test_docx_render_applies_theme_cover_and_toc(tmp_path):
    meta, body = markup.split_front_matter(SAMPLE)
    blocks = markup.document_blocks(markup.parse_blocks(body))
    theme = themes.load_theme("academic-hebat")
    out = tmp_path / "doc.docx"
    report = render_docx(blocks, meta, theme, out, base_dir=tmp_path, toc_pages={0: 3, 1: 4})
    document = docx.Document(str(out))
    texts = [p.text for p in document.paragraphs]
    assert "LAPORAN UJI" in texts
    assert any(t.startswith("Pendahuluan\t3") for t in texts)
    assert "Daftar Isi" in texts
    assert report.tables == 1 and report.headings == [(1, "Pendahuluan"), (1, "Data")]
    assert document.styles["Normal"].font.name == "Times New Roman"
    assert any("Tabel 1. Ringkasan" in t for t in texts)


def test_pptx_render_numbers_lists_and_splits_long_tables(tmp_path):
    rows = "\n".join(f"| r{i} | {i} |" for i in range(20))
    source = "# Angka\n\n| A | B |\n|---|---|\n" + rows + "\n\n# Daftar\n\n1. satu\n2. dua\n"
    meta = {"title": "Deck"}
    slides = markup.to_slides(markup.parse_blocks(source))
    out = tmp_path / "deck.pptx"
    report = render_pptx(slides, meta, themes.load_theme("professional"), out, base_dir=tmp_path)
    prs = pptx.Presentation(str(out))
    assert len(prs.slides) == report.slides == 1 + 3 + 1
    assert report.split_slides == 2
    xml = prs.slides[-1].shapes[-1]._element.xml if prs.slides[-1].shapes else ""
    assert "buAutoNum" in "".join(shape._element.xml for shape in prs.slides[-1].shapes) or "buAutoNum" in xml


def test_pptx_splits_slides_with_several_visuals(tmp_path):
    source = "# Campur\n\n| A |\n|---|\n| 1 |\n\n```python\nprint(1)\n```\n"
    slides = markup.to_slides(markup.parse_blocks(source))
    report = render_pptx(slides, {}, themes.load_theme("minimal"), tmp_path / "d.pptx", base_dir=tmp_path)
    assert report.slides == 2


def test_heading_pages_skip_the_table_of_contents():
    pages = ["cover", "Daftar Isi Pendahuluan Metode", "Pendahuluan teks", "lain", "Metode teks"]
    found = _heading_pages(pages, [(1, "Pendahuluan"), (1, "Metode")], skip=1)
    assert found == {0: 3, 1: 5}


def test_theme_extraction_samples_used_colors_and_fixes_contrast(tmp_path):
    from pptx.dml.color import RGBColor
    from pptx.util import Inches, Pt

    prs = pptx.Presentation()
    for _ in range(2):
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        bar = slide.shapes.add_shape(1, Inches(0), Inches(0), Inches(3), Inches(1))
        bar.fill.solid()
        bar.fill.fore_color.rgb = RGBColor.from_string("E4572E")
        box = slide.shapes.add_textbox(Inches(1), Inches(2), Inches(6), Inches(2))
        run = box.text_frame.paragraphs[0].add_run()
        run.text = "Judul besar"
        run.font.size = Pt(36)
        run.font.name = "Arial"
        run.font.color.rgb = RGBColor.from_string("17324D")
        body = box.text_frame.add_paragraph().add_run()
        body.text = "Isi paragraf dengan warna yang terlalu pucat"
        body.font.size = Pt(16)
        body.font.color.rgb = RGBColor.from_string("EEEEEE")
    path = tmp_path / "canva-export.pptx"
    prs.save(str(path))
    overrides, evidence = extract_theme(path)
    colors = overrides["colors"]
    assert colors["accent"] == "#E4572E"
    assert colors["slide_title"] == "#17324D"
    assert contrast(colors["slide_text"], colors["slide_background"]) >= 4.5
    assert evidence["usage"]["slides"] == 2
    assert any("contrast" in warning for warning in evidence["warnings"])


def test_tools_report_errors_instead_of_raising():
    from xninetzy.tools.ecosystem.document_studio_tools import DOCUMENT_STUDIO_TOOLS

    tools = {tool.name: tool for tool in DOCUMENT_STUDIO_TOOLS}
    result = tools["artifact_render"].invoke({"markdown": "# x", "formats": ["exe"]})
    assert result["status"] == "error"
    assert tools["artifact_theme_get"].invoke({"name": "missing-theme"})["status"] == "error"
    assert {t["name"] for t in tools["artifact_theme_list"].invoke({})["themes"]} >= {"academic-hebat"}


def test_deck_render_asks_owner_for_brief_and_canva_reference_first(tmp_path):
    from xninetzy.tools.ecosystem.document_studio_tools import DOCUMENT_STUDIO_TOOLS

    render = {tool.name: tool for tool in DOCUMENT_STUDIO_TOOLS}["artifact_render"]
    pending = render.invoke({"markdown": "# x", "formats": ["docx", "pptx"], "output_name": "gate"})
    assert pending["status"] == "awaiting_input"
    assert pending["rendered"] is False
    assert pending["formats"] == ["pptx"]
    assert any("Canva" in question for question in pending["ask_owner"])
    assert any("export-design" in step for step in pending["canva_reference_flow"])
    assert "academic-hebat" in pending["themes"]
    confirmed = render.invoke({"markdown": "# x", "formats": ["pptx", "exe"], "deck_brief_confirmed": True})
    assert confirmed["status"] == "error"
    assert "unsupported formats" in confirmed["message"]


@pytest.mark.skipif(office_binary() is None, reason="LibreOffice is not installed")
def test_render_end_to_end_writes_all_formats_with_previews():
    pytest.importorskip("pypdfium2")
    from xninetzy.integrations.document_studio import studio

    manifest = studio.render(markdown=SAMPLE, formats=["docx", "pdf", "pptx", "slides_pdf"], theme="academic-hebat", output_name="uji")
    assert manifest["status"] in ("ok", "warning")
    for key in ("docx", "pdf", "pptx", "slides_pdf"):
        assert Path(manifest["files"][key]).is_file()
    assert Path(manifest["previews"]["pdf"]["contact_sheet"]).is_file()
    assert manifest["qa"]["pdf"]["pages"] >= 3
    saved = json.loads((Path(manifest["output_dir"]) / "manifest.json").read_text())
    assert saved["theme"] == "academic-hebat"
    docx_texts = [p.text for p in docx.Document(manifest["files"]["docx"]).paragraphs]
    toc_line = next(t for t in docx_texts if t.startswith("Pendahuluan\t"))
    assert toc_line.split("\t")[1].isdigit()
