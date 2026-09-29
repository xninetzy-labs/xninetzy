from __future__ import annotations

import pytest

from xninetzy.integrations.moviepy.reframe import ReframeError, plan_reframe


def test_landscape_to_vertical_crop_covers_target():
    plan = plan_reframe(1920, 1080, 1080, 1920, mode="crop")
    assert plan.crop_x2 - plan.crop_x1 == 1080
    assert plan.crop_y2 - plan.crop_y1 == 1920
    assert plan.scaled_width >= 1080 and plan.scaled_height >= 1920
    assert plan.crop_x1 >= 0 and plan.crop_y1 >= 0
    assert plan.crop_x2 <= plan.scaled_width and plan.crop_y2 <= plan.scaled_height


def test_vertical_to_landscape_pad_centers():
    plan = plan_reframe(1080, 1920, 1920, 1080, mode="pad")
    assert plan.scaled_width <= 1920 and plan.scaled_height <= 1080
    assert plan.pad_x >= 0 and plan.pad_y >= 0
    assert plan.pad_x * 2 + plan.scaled_width <= 1920 + 1


def test_even_dimensions_enforced():
    plan = plan_reframe(1919, 1081, 1081, 1921, mode="crop")
    for value in (
        plan.target_width, plan.target_height,
        plan.scaled_width, plan.scaled_height,
        plan.crop_x1, plan.crop_y1,
    ):
        assert value % 2 == 0, value


def test_unknown_mode_rejected():
    with pytest.raises(ReframeError):
        plan_reframe(100, 100, 50, 50, mode="warp")


def test_nonpositive_rejected():
    with pytest.raises(ReframeError):
        plan_reframe(0, 100, 50, 50, mode="crop")
