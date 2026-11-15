"""Reject stale local wheels before packaging a runtime image.

Run with Python -I so the checkout cannot shadow the installed distribution.
Only source/assets are compared; no application configuration or database opens.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path


def compare_package_files(source: Path, installed: Path) -> dict:
    if source.resolve() == installed.resolve():
        raise ValueError("installed package is shadowed by source")
    if not source.is_dir() or not installed.is_dir():
        raise ValueError("both package roots must exist")

    def inventory(root, *, source_only_exclusions=False):
        return {
            path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in root.rglob("*")
            if path.is_file() and path.suffix in {".py", ".json", ".sql"}
            and not (source_only_exclusions and "tests" in path.relative_to(root).parts)
        }

    # Match pyproject's explicit xninetzy/**/tests/** wheel exclusion.
    expected, actual = inventory(source, source_only_exclusions=True), inventory(installed)
    missing = sorted(expected.keys() - actual.keys())
    extra = sorted(actual.keys() - expected.keys())
    changed = sorted(name for name in expected.keys() & actual.keys() if expected[name] != actual[name])
    return {"ok": bool(expected) and not (missing or extra or changed), "files_checked": len(expected),
            "missing": missing, "extra": extra, "changed": changed}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    args = parser.parse_args()
    spec = importlib.util.find_spec("xninetzy")
    if spec is None or spec.origin is None:
        raise SystemExit("installed xninetzy package unavailable")
    result = compare_package_files(args.source.resolve(), Path(spec.origin).resolve().parent)
    print(json.dumps(result, sort_keys=True))
    return int(not result["ok"])


if __name__ == "__main__":
    raise SystemExit(main())
