from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image

from xninetzy.tools.ecosystem.vision_tools import (
    image_compare,
    image_crop,
    image_inspect,
    image_layout,
    image_ocr,
    image_preprocess,
    image_regions,
)


def _make_image(path: Path, width: int = 80, height: int = 80, channels: int = 3) -> Path:
    arr = (np.random.rand(height, width, channels) * 255).astype(np.uint8)
    Image.fromarray(arr, mode="RGB").save(path)
    return path


def _invoke(tool, **kwargs) -> dict:
    return json.loads(tool.invoke(kwargs))


def test_image_inspect_returns_metadata(tmp_path):
    src = _make_image(tmp_path / "a.png")
    out = _invoke(image_inspect, path=str(src))
    assert out["width"] == 80
    assert out["height"] == 80
    assert out["channels"] == 3
    assert out["format"] == "png"
    assert "mean_rgb" in out["stats"]


def test_image_inspect_handles_missing(tmp_path):
    out = _invoke(image_inspect, path=str(tmp_path / "missing.png"))
    assert "error" in out


def test_image_preprocess_grayscale(tmp_path):
    src = _make_image(tmp_path / "a.png")
    out = _invoke(
        image_preprocess,
        path=str(src),
        output_path=str(tmp_path / "out.png"),
        grayscale=True,
    )
    assert out["applied"] == ["grayscale"]
    assert Path(out["output"]).exists()


def test_image_preprocess_threshold_modes(tmp_path):
    arr = np.zeros((80, 80, 3), dtype=np.uint8)
    arr[20:60, 20:60] = 255
    src = tmp_path / "bi.png"
    Image.fromarray(arr, mode="RGB").save(src)
    for mode in ("otsu", "adaptive"):
        out = _invoke(
            image_preprocess,
            path=str(src),
            output_path=str(tmp_path / f"{mode}.png"),
            threshold=mode,
        )
        assert mode in out["applied"]
        assert Path(out["output"]).exists()


def test_image_crop_bounds(tmp_path):
    src = _make_image(tmp_path / "a.png")
    out = _invoke(
        image_crop,
        path=str(src),
        x=10, y=10, width=20, height=20,
        output_path=str(tmp_path / "crop.png"),
    )
    assert out["bounds"] == [10, 10, 30, 30]
    assert out["shape"][0] == 20
    assert out["shape"][1] == 20
    assert Path(out["output"]).exists()


def test_image_crop_rejects_empty(tmp_path):
    src = _make_image(tmp_path / "a.png", width=80, height=80)
    out = _invoke(
        image_crop,
        path=str(src),
        x=200, y=200, width=50, height=50,
    )
    assert "error" in out


def test_image_regions_contours(tmp_path):
    src = _make_image(tmp_path / "a.png")
    out = _invoke(image_regions, path=str(src), method="contours", limit=20)
    assert out["method"] == "contours"
    assert "region_count" in out
    assert "regions" in out


def test_image_compare_identical_returns_high_score(tmp_path):
    src = _make_image(tmp_path / "a.png")
    out = _invoke(image_compare, path_a=str(src), path_b=str(src), metric="diff")
    assert out["score"] >= 99.0


def test_image_compare_histogram(tmp_path):
    a = _make_image(tmp_path / "a.png")
    b = _make_image(tmp_path / "b.png")
    out = _invoke(image_compare, path_a=str(a), path_b=str(b), metric="histogram")
    assert out["metric"] == "histogram"
    assert "score" in out


def test_image_compare_handles_missing(tmp_path):
    src = _make_image(tmp_path / "a.png")
    out = _invoke(image_compare, path_a=str(src), path_b=str(tmp_path / "missing.png"))
    assert "error" in out


def test_image_layout_emits_shape_and_stats(tmp_path):
    src = _make_image(tmp_path / "a.png")
    out = _invoke(image_layout, path=str(src))
    assert out["shape"] == [80, 80]
    assert "edge_density" in out
    assert "horizontal_lines" in out
    assert "vertical_lines" in out


def test_image_ocr_reports_tesseract_absence(tmp_path):
    src = _make_image(tmp_path / "a.png")
    out = _invoke(image_ocr, path=str(src))
    assert "error" in out or "regions" in out
