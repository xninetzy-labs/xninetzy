from __future__ import annotations

from xninetzy.context.reasoning.critic import (
    CriticDefect,
    CriticVerdict,
    CRITIC_SEVERITY_BLOCKER,
    CRITIC_SEVERITY_INFO,
    CRITIC_SEVERITY_WARNING,
    CRITIC_VERDICT_FAIL,
    CRITIC_VERDICT_PASS,
    CRITIC_VERDICT_WARN,
    critique_outcome,
)
from xninetzy.context.reasoning.depth import (
    REASONING_DEPTH_COMPLEX,
    REASONING_DEPTH_HIGH_RISK,
    REASONING_DEPTH_ROUTINE,
    REASONING_DEPTH_TRIVIAL,
    ReasoningDepth,
    classify_request_depth,
    is_terminal_depth,
)
from xninetzy.context.reasoning.stop import (
    AntiLoopSignal,
    StopDecision,
    STOP_CONTINUE,
    STOP_HALT,
    STOP_REPLAN,
    should_stop,
)

PACKAGE_MARKER: str = "xninetzy.context.reasoning"

__all__ = [
    "AntiLoopSignal",
    "CRITIC_SEVERITY_BLOCKER",
    "CRITIC_SEVERITY_INFO",
    "CRITIC_SEVERITY_WARNING",
    "CRITIC_VERDICT_FAIL",
    "CRITIC_VERDICT_PASS",
    "CRITIC_VERDICT_WARN",
    "CriticDefect",
    "CriticVerdict",
    "PACKAGE_MARKER",
    "REASONING_DEPTH_COMPLEX",
    "REASONING_DEPTH_HIGH_RISK",
    "REASONING_DEPTH_ROUTINE",
    "REASONING_DEPTH_TRIVIAL",
    "ReasoningDepth",
    "STOP_CONTINUE",
    "STOP_HALT",
    "STOP_REPLAN",
    "StopDecision",
    "classify_request_depth",
    "critique_outcome",
    "is_terminal_depth",
    "should_stop",
]
