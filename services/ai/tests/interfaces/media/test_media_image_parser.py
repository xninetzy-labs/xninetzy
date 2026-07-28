from PIL import Image

from app.xninetzy.interfaces.media import image_parser


def test_parse_image_returns_ocr_text(tmp_path, monkeypatch):
    path = tmp_path / "screen.png"
    Image.new("RGB", (320, 120), "white").save(path)
    monkeypatch.setattr(image_parser, "_run_ocr", lambda image, languages: "Halo OCR")

    out = image_parser.parse_image(
        str(path), mime_type="image/png", filename="screen.png"
    )
    assert out["error"] is None
    assert out["text"] == "Halo OCR"
    assert out["width"] == 320
    assert out["height"] == 120


def test_parse_image_reports_no_text(tmp_path, monkeypatch):
    path = tmp_path / "photo.jpg"
    Image.new("RGB", (10, 10), "black").save(path)
    monkeypatch.setattr(image_parser, "_run_ocr", lambda image, languages: "")

    out = image_parser.parse_image(str(path), filename="photo.jpg")
    assert out["error"]
    assert "model vision" in out["error"]


def test_parse_image_rejects_unsupported_type(tmp_path):
    path = tmp_path / "animation.gif"
    path.write_bytes(b"GIF89a")
    out = image_parser.parse_image(str(path), mime_type="image/gif")
    assert out["error"]
    assert "belum didukung" in out["error"]
