from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class RoutingAudit:
    chosen_route: str
    candidates: tuple[str, ...]
    alternative_routes: tuple[str, ...]
    suboptimal: bool
    reason: str
    notes: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "chosen_route": self.chosen_route,
            "candidates": list(self.candidates),
            "alternative_routes": list(self.alternative_routes),
            "suboptimal": self.suboptimal,
            "reason": self.reason,
            "notes": list(self.notes),
        }


def evaluate_routing(
    *,
    chosen: str,
    candidates: tuple[str, ...],
    success_history: dict[str, int] | None = None,
    failure_history: dict[str, int] | None = None,
) -> RoutingAudit:
    history = {
        k: int(v)
        for k, v in (success_history or {}).items()
    }
    failures = {
        k: int(v)
        for k, v in (failure_history or {}).items()
    }
    alternatives = tuple(c for c in candidates if c != chosen)
    chosen_success = history.get(chosen, 0)
    chosen_fail = failures.get(chosen, 0)
    chosen_total = chosen_success + chosen_fail
    notes: list[str] = []
    suboptimal = False
    reason = "chosen route has positive history"
    for alt in alternatives:
        alt_success = history.get(alt, 0)
        alt_fail = failures.get(alt, 0)
        alt_total = alt_success + alt_fail
        if alt_total > 0 and alt_success / alt_total > (
            chosen_success / chosen_total if chosen_total else 0.0
        ) + 0.2:
            suboptimal = True
            reason = f"alternative {alt} has higher success rate"
            notes.append(
                f"chosen success={chosen_success}/{chosen_total}; "
                f"alt success={alt_success}/{alt_total}"
            )
            break
    if not chosen_total and alternatives:
        notes.append("no history available; default route used")
    return RoutingAudit(
        chosen_route=chosen,
        candidates=candidates,
        alternative_routes=alternatives,
        suboptimal=suboptimal,
        reason=reason,
        notes=tuple(notes),
    )
