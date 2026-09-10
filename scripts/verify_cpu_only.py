"""CPU-only runtime verifier.

Prints a JSON snapshot proving the AI runtime is pure CPU: no CUDA torch, no
forbidden GPU distributions, FAISS on its CPU build. Exit non-zero if the guard
rejects the environment.

    uv run python scripts/verify_cpu_only.py
"""

from __future__ import annotations

import json
import sys

from app.xninetzy.runtime.cpu_guard import validate_cpu_only_runtime


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

    runtime["ok"] = True
    print(json.dumps(runtime, indent=2, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
