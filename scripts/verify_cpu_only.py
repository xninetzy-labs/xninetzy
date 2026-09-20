"""CPU-only runtime verifier.

Prints a JSON snapshot proving the AI runtime is pure CPU: no CUDA torch, no
forbidden GPU distributions, FAISS on its CPU build. Exit non-zero if the guard
rejects the environment.

Also runs a skill catalog healthcheck. Default mode is warn-only so the gate
does not fail on the known 78 invalid SKILL.md files; flip
XNINETZY_SKILL_HEALTHCHECK_STRICT=true to fail on invalid frontmatter (after
``python scripts/repair_skill_yaml.py --inplace`` migrates the catalog).

    uv run python scripts/verify_cpu_only.py
"""

from __future__ import annotations

import json
import os
import sys

from xninetzy.runtime.cpu_guard import validate_cpu_only_runtime


def _skill_healthcheck() -> dict:
    try:
        from xninetzy.skills.tools import skill_healthcheck
    except Exception as exc:
        return {"ok": False, "skipped": True, "error": type(exc).__name__}
    report = skill_healthcheck.invoke({})
    invalid = 0
    valid = 0
    for line in (report or "").splitlines():
        low = line.lower()
        if low.startswith("invalid"):
            try:
                invalid = int(line.rsplit(":", 1)[1].strip())
            except ValueError:
                pass
        elif low.startswith("valid"):
            try:
                valid = int(line.rsplit(":", 1)[1].strip())
            except ValueError:
                pass
    return {"ok": True, "valid": valid, "invalid": invalid, "report": report}


def main() -> int:
    try:
        runtime: dict[str, object] = validate_cpu_only_runtime()
    except RuntimeError as e:
        print(json.dumps({"ok": False, "error": str(e)}, indent=2))
        return 1

    try:
        import faiss

        runtime["faiss_version"] = getattr(faiss, "__version__", "unknown")
        runtime["faiss_gpu_api"] = hasattr(faiss, "StandardGpuResources")
    except Exception:  # pragma: no cover - faiss optional
        runtime["faiss_version"] = None
        runtime["faiss_gpu_api"] = False

    skill = _skill_healthcheck()
    strict = os.environ.get("XNINETZY_SKILL_HEALTHCHECK_STRICT", "").strip().lower() in {
        "1",
        "true",
        "yes",
    }
    runtime["skill_healthcheck"] = skill
    runtime["skill_strict"] = strict
    runtime["ok"] = True
    print(json.dumps(runtime, indent=2, ensure_ascii=False, default=str))

    if strict and skill.get("ok") and skill.get("invalid", 0) > 0:
        print(
            f"\nskill healthcheck STRICT: {skill['invalid']} invalid frontmatter; failing.",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
