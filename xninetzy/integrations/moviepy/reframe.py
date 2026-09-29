from __future__ import annotations

from dataclasses import dataclass

REFRAME_MODES = ("crop", "pad")


class ReframeError(ValueError):
    pass


def _even(value: int) -> int:
    value = int(value)
    return value - (value % 2)


@dataclass(frozen=True, slots=True)
class ReframePlan:
    mode: str
    source_width: int
    source_height: int
    target_width: int
    target_height: int
    scaled_width: int
    scaled_height: int
    crop_x1: int
    crop_y1: int
    crop_x2: int
    crop_y2: int
    pad_x: int
    pad_y: int

    def to_dict(self) -> dict:
        return {
            "mode": self.mode,
            "source": {"width": self.source_width, "height": self.source_height},
            "target": {"width": self.target_width, "height": self.target_height},
            "scaled": {"width": self.scaled_width, "height": self.scaled_height},
            "crop": {
                "x1": self.crop_x1,
                "y1": self.crop_y1,
                "x2": self.crop_x2,
                "y2": self.crop_y2,
            },
            "pad": {"x": self.pad_x, "y": self.pad_y},
        }


def plan_reframe(
    source_width: int,
    source_height: int,
    target_width: int,
    target_height: int,
    mode: str = "crop",
) -> ReframePlan:
    if mode not in REFRAME_MODES:
        raise ReframeError(f"unknown reframe mode '{mode}'; allowed: {', '.join(REFRAME_MODES)}")
    if min(source_width, source_height, target_width, target_height) <= 0:
        raise ReframeError("reframe dimensions must be positive")

    target_width = _even(target_width)
    target_height = _even(target_height)
    if target_width <= 0 or target_height <= 0:
        raise ReframeError("target dimensions too small after even-rounding")

    if mode == "crop":
        scale = max(target_width / source_width, target_height / source_height)
        scaled_width = _even(round(source_width * scale))
        scaled_height = _even(round(source_height * scale))
        scaled_width = max(scaled_width, target_width)
        scaled_height = max(scaled_height, target_height)
        crop_x1 = _even((scaled_width - target_width) // 2)
        crop_y1 = _even((scaled_height - target_height) // 2)
        crop_x2 = crop_x1 + target_width
        crop_y2 = crop_y1 + target_height
        pad_x = 0
        pad_y = 0
    else:
        scale = min(target_width / source_width, target_height / source_height)
        scaled_width = _even(round(source_width * scale))
        scaled_height = _even(round(source_height * scale))
        scaled_width = max(scaled_width, 2)
        scaled_height = max(scaled_height, 2)
        crop_x1 = 0
        crop_y1 = 0
        crop_x2 = scaled_width
        crop_y2 = scaled_height
        pad_x = max(0, (target_width - scaled_width) // 2)
        pad_y = max(0, (target_height - scaled_height) // 2)

    return ReframePlan(
        mode=mode,
        source_width=source_width,
        source_height=source_height,
        target_width=target_width,
        target_height=target_height,
        scaled_width=scaled_width,
        scaled_height=scaled_height,
        crop_x1=crop_x1,
        crop_y1=crop_y1,
        crop_x2=crop_x2,
        crop_y2=crop_y2,
        pad_x=pad_x,
        pad_y=pad_y,
    )
