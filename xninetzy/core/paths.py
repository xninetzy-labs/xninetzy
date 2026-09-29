from __future__ import annotations

from pathlib import Path

from xninetzy.core.config import Settings, get_settings


class ArtifactPathError(ValueError):
    pass


_WRITE_ROOT_KEYS = (
    "OUTPUT_DIR",
    "GENERATED_DOCUMENTS_DIR",
    "RESEARCH_OUTPUT_DIR",
    "UNTRACKED_OUTPUT_DIR",
    "VIDEO_OUTPUT_DIR",
    "DATA_DIR",
)


def _resolved(value: str) -> Path | None:
    if not value:
        return None
    try:
        return Path(value).expanduser().resolve()
    except (OSError, RuntimeError, ValueError):
        return None


def artifact_write_roots(settings: Settings | None = None) -> tuple[Path, ...]:
    current = settings or get_settings()
    roots: list[Path] = []
    for key in _WRITE_ROOT_KEYS:
        resolved = _resolved(str(getattr(current, key, "") or ""))
        if resolved is not None and resolved not in roots:
            roots.append(resolved)
    return tuple(roots)


def _within(candidate: Path, root: Path) -> bool:
    return candidate == root or root in candidate.parents


def resolve_artifact_output(
    path: str | Path,
    *,
    settings: Settings | None = None,
    create_parents: bool = False,
    extra_roots: tuple[str | Path, ...] = (),
) -> Path:
    current = settings or get_settings()
    raw = str(path or "").strip()
    if not raw:
        raise ArtifactPathError("output path must not be empty")
    if "\x00" in raw:
        raise ArtifactPathError("output path contains a null byte")
    resolved = Path(raw).expanduser().resolve()
    if getattr(current, "ARTIFACT_ALLOWLIST", True):
        roots = list(artifact_write_roots(current))
        for extra in extra_roots:
            extra_resolved = _resolved(str(extra))
            if extra_resolved is not None and extra_resolved not in roots:
                roots.append(extra_resolved)
        if not any(_within(resolved, root) for root in roots):
            allowed = ", ".join(str(root) for root in roots) or "(none configured)"
            raise ArtifactPathError(
                f"write outside allowed artifact roots is blocked (ARTIFACT_ALLOWLIST). "
                f"path={resolved}; allowed roots: {allowed}"
            )
    if create_parents:
        resolved.parent.mkdir(parents=True, exist_ok=True)
    return resolved


def is_within_artifact_roots(path: str | Path, settings: Settings | None = None) -> bool:
    try:
        resolve_artifact_output(path, settings=settings)
        return True
    except ArtifactPathError:
        return False
