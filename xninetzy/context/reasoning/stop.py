from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


STOP_CONTINUE: str = "continue"
STOP_HALT: str = "halt"
STOP_REPLAN: str = "replan"


@dataclass(frozen=True, slots=True)
class AntiLoopSignal:
    fingerprint: str
    repeat_count: int
    window_size: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "fingerprint": self.fingerprint,
            "repeat_count": self.repeat_count,
            "window_size": self.window_size,
        }


@dataclass(frozen=True, slots=True)
class StopDecision:
    outcome: str
    reason: str
    iteration: int
    anti_loop: AntiLoopSignal | None = None
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def is_terminal(self) -> bool:
        return self.outcome in (STOP_HALT, STOP_REPLAN)

    def to_dict(self) -> dict[str, Any]:
        return {
            "outcome": self.outcome,
            "reason": self.reason,
            "iteration": self.iteration,
            "anti_loop": self.anti_loop.to_dict() if self.anti_loop else None,
            "details": dict(self.details),
        }


def _fingerprint(step: dict[str, Any]) -> str:
    keys = ("hypothesis", "tool", "outcome")
    parts: list[str] = []
    for key in keys:
        value = step.get(key)
        parts.append(f"{key}={value!r}")
    return "|".join(parts)


def _detect_loop(steps: tuple[dict[str, Any], ...], window: int) -> AntiLoopSignal | None:
    if not steps or window <= 0:
        return None
    recent = list(steps[-window:])
    fp = _fingerprint(recent[-1])
    repeat = sum(1 for step in recent if _fingerprint(step) == fp)
    if repeat >= max(2, window // 2):
        return AntiLoopSignal(fingerprint=fp, repeat_count=repeat, window_size=window)
    return None


def should_stop(
    *,
    iteration: int,
    steps: tuple[dict[str, Any], ...] = (),
    success_criteria_met: bool = False,
    critical_uncertainty: float = 1.0,
    min_iterations: int = 1,
    max_iterations: int = 8,
    anti_loop_window: int = 4,
    force_replan: bool = False,
) -> StopDecision:
    if force_replan:
        return StopDecision(
            outcome=STOP_REPLAN,
            reason="force_replan requested",
            iteration=iteration,
            details={"forced": True},
        )
    loop_signal = _detect_loop(steps, anti_loop_window)
    if loop_signal is not None and loop_signal.repeat_count >= max(2, anti_loop_window // 2):
        return StopDecision(
            outcome=STOP_REPLAN,
            reason=f"anti-loop trigger: fingerprint repeated {loop_signal.repeat_count} times in window {loop_signal.window_size}",
            iteration=iteration,
            anti_loop=loop_signal,
        )
    if iteration >= max_iterations:
        return StopDecision(
            outcome=STOP_HALT,
            reason=f"max_iterations {max_iterations} reached",
            iteration=iteration,
        )
    if success_criteria_met and iteration >= min_iterations and critical_uncertainty <= 0.3:
        return StopDecision(
            outcome=STOP_HALT,
            reason="success criteria met and uncertainty resolved",
            iteration=iteration,
            details={"critical_uncertainty": critical_uncertainty},
        )
    if critical_uncertainty >= 0.95 and iteration >= max_iterations - 1:
        return StopDecision(
            outcome=STOP_HALT,
            reason="critical uncertainty cannot be resolved within iteration budget",
            iteration=iteration,
            details={"critical_uncertainty": critical_uncertainty},
        )
    return StopDecision(
        outcome=STOP_CONTINUE,
        reason="continue reasoning",
        iteration=iteration,
        details={"critical_uncertainty": critical_uncertainty},
    )
