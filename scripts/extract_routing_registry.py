#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from xninetzy.context.registry_extractor import write_outputs  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Xninetzy routing registry extractor.")
    parser.add_argument("--write", action="store_true", help="Persist the five JSON manifests to disk.")
    parser.add_argument(
        "--output-root",
        default="data/registry",
        help="Output directory (default: data/registry).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=True,
        help="Print a one-line summary to stdout (default: on).",
    )
    parser.add_argument(
        "--quiet",
        dest="verbose",
        action="store_false",
        help="Disable stdout summary.",
    )
    args = parser.parse_args()

    payload = write_outputs(args.output_root, write=args.write, verbose=args.verbose)
    if args.write:
        manifest_sha = payload["shas"].get("manifest", "")
        (Path(args.output_root) / "routing_manifest.sha256").write_text(
            manifest_sha + "\n", encoding="utf-8"
        )
        if args.verbose:
            print(
                f"Wrote 5 manifests under {args.output_root}; "
                f"manifest sha256={manifest_sha}",
                file=sys.stdout,
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())
