from __future__ import annotations

import time

from xninetzy.observability.perf import measure, reset, snapshot


def test_measure_records_elapsed():
    reset()
    with measure("smoke"):
        time.sleep(0.001)
    snap = snapshot()
    assert "smoke" in snap
    assert snap["smoke"]["samples"] == 1
    assert snap["smoke"]["avg_ms"] > 0
    assert snap["smoke"]["max_ms"] >= snap["smoke"]["avg_ms"]


def test_measure_handles_exceptions():
    reset()
    try:
        with measure("explode"):
            raise RuntimeError("boom")
    except RuntimeError:
        pass
    snap = snapshot()
    assert snap["explode"]["samples"] == 1


def test_snapshot_empty_when_no_measurements():
    reset()
    snap = snapshot()
    assert snap == {}


def test_reset_clears_all():
    with measure("temp"):
        pass
    reset()
    snap = snapshot()
    assert snap == {}
