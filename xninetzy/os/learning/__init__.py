from .pedagogy import (
    decide_hint,
    record_hint,
    detect_misconception,
    calibrate_confidence,
    detect_dependency,
    scaffold_fade,
    next_action,
)
from .mastery import (
    update_mastery,
    mastery_gaps,
    mastery_review_queue,
    independence_score,
)

__all__ = [
    "decide_hint",
    "record_hint",
    "detect_misconception",
    "calibrate_confidence",
    "detect_dependency",
    "scaffold_fade",
    "next_action",
    "update_mastery",
    "mastery_gaps",
    "mastery_review_queue",
    "independence_score",
]
