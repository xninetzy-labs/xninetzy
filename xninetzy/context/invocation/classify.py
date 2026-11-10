from __future__ import annotations

from dataclasses import dataclass


SIDE_EFFECT_READ_ONLY: str = "read_only"
SIDE_EFFECT_IDEMPOTENT_WRITE: str = "idempotent_write"
SIDE_EFFECT_NON_IDEMPOTENT_WRITE: str = "non_idempotent_write"
SIDE_EFFECT_EXTERNAL: str = "external_side_effect"
SIDE_EFFECT_IRREVERSIBLE: str = "irreversible"

VALID_SIDE_EFFECT_CLASSES: frozenset[str] = frozenset(
    {
        SIDE_EFFECT_READ_ONLY,
        SIDE_EFFECT_IDEMPOTENT_WRITE,
        SIDE_EFFECT_NON_IDEMPOTENT_WRITE,
        SIDE_EFFECT_EXTERNAL,
        SIDE_EFFECT_IRREVERSIBLE,
    }
)


@dataclass(frozen=True, slots=True)
class SideEffectClass:
    name: str
    requires_approval: bool
    requires_idempotency_key: bool
    allowed_for_unverified: bool


SIDE_EFFECT_TABLE: dict[str, SideEffectClass] = {
    SIDE_EFFECT_READ_ONLY: SideEffectClass(
        name=SIDE_EFFECT_READ_ONLY,
        requires_approval=False,
        requires_idempotency_key=False,
        allowed_for_unverified=True,
    ),
    SIDE_EFFECT_IDEMPOTENT_WRITE: SideEffectClass(
        name=SIDE_EFFECT_IDEMPOTENT_WRITE,
        requires_approval=False,
        requires_idempotency_key=True,
        allowed_for_unverified=True,
    ),
    SIDE_EFFECT_NON_IDEMPOTENT_WRITE: SideEffectClass(
        name=SIDE_EFFECT_NON_IDEMPOTENT_WRITE,
        requires_approval=False,
        requires_idempotency_key=True,
        allowed_for_unverified=False,
    ),
    SIDE_EFFECT_EXTERNAL: SideEffectClass(
        name=SIDE_EFFECT_EXTERNAL,
        requires_approval=False,
        requires_idempotency_key=True,
        allowed_for_unverified=False,
    ),
    SIDE_EFFECT_IRREVERSIBLE: SideEffectClass(
        name=SIDE_EFFECT_IRREVERSIBLE,
        requires_approval=True,
        requires_idempotency_key=True,
        allowed_for_unverified=False,
    ),
}


def classify_side_effect(name: str | None) -> SideEffectClass:
    """Resolve a declared class; reject malformed explicit classifications.

    ``None`` retains the legacy read-only default for existing callers. This
    classifier does not verify that a valid caller declaration matches the
    actual operation; canonical capability policy must enforce that separately.
    """
    if name is None:
        return SIDE_EFFECT_TABLE[SIDE_EFFECT_READ_ONLY]
    key = str(name).strip().lower()
    if key in SIDE_EFFECT_TABLE:
        return SIDE_EFFECT_TABLE[key]
    raise ValueError("invalid explicit side_effect class")


def side_effect_names() -> tuple[str, ...]:
    return tuple(sorted(SIDE_EFFECT_TABLE))
