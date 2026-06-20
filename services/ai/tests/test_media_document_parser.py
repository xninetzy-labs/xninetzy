import json

from app.xninetzy.interfaces.media.document_parser import parse_document


def test_parse_txt(tmp_path):
    p = tmp_path / "note.txt"
    p.write_text("Hello Xninetzy second brain", encoding="utf-8")
    out = parse_document(str(p), mime_type="text/plain", filename="note.txt")
    assert out["error"] is None
    assert "Xninetzy" in out["text"]
    assert out["kind"] == "txt"
    assert out["char_count"] > 0


def test_parse_markdown(tmp_path):
    p = tmp_path / "doc.md"
    p.write_text("# Title\n\nIsi catatan belajar", encoding="utf-8")
    out = parse_document(str(p))
    assert out["error"] is None
    assert "Isi catatan" in out["text"]


def test_parse_csv(tmp_path):
    p = tmp_path / "data.csv"
    p.write_text("a,b\n1,2\n3,4", encoding="utf-8")
    out = parse_document(str(p))
    assert out["error"] is None
    assert "1,2" in out["text"]


def test_parse_json_pretty(tmp_path):
    p = tmp_path / "x.json"
    p.write_text(json.dumps({"topic": "graph rag"}), encoding="utf-8")
    out = parse_document(str(p))
    assert out["error"] is None
    assert "graph rag" in out["text"]


def test_missing_file():
    out = parse_document("/tmp/does-not-exist-xyz.txt", filename="x.txt")
    assert out["error"]
    assert out["text"] == ""


def test_unsupported_extension(tmp_path):
    p = tmp_path / "thing.bin"
    p.write_bytes(b"\x00\x01\x02")
    out = parse_document(str(p), mime_type="application/octet-stream", filename="thing.bin")
    assert out["error"]
    assert "belum didukung" in out["error"].lower()


def test_mime_used_when_no_extension(tmp_path):
    p = tmp_path / "noext"
    p.write_text("plain content here", encoding="utf-8")
    out = parse_document(str(p), mime_type="text/plain", filename="noext")
    assert out["error"] is None
    assert "plain content" in out["text"]


def test_empty_document(tmp_path):
    p = tmp_path / "empty.txt"
    p.write_text("   \n  ", encoding="utf-8")
    out = parse_document(str(p))
    assert out["error"]
