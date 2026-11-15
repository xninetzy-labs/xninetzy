from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from xninetzy.core.config import expand_paths, get_settings


_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_AUDIT_SCRIPT = _REPO_ROOT / "scripts" / "mcp_audit.py"


def _cmd_init(_args: argparse.Namespace) -> int:
    settings = expand_paths(get_settings())
    created: list[str] = []
    for key in (
        "DATA_DIR",
        "OUTPUT_DIR",
        "GENERATED_DOCUMENTS_DIR",
        "RESEARCH_OUTPUT_DIR",
        "UNTRACKED_OUTPUT_DIR",
        "HEBAT_DATA_DIR",
        "OBSIDIAN_VAULT_HOST_PATH",
    ):
        raw = getattr(settings, key, "")
        if not raw:
            continue
        target = Path(raw)
        if target.exists():
            continue
        try:
            target.mkdir(parents=True, exist_ok=True)
            created.append(str(target))
        except OSError as exc:
            print(f"warn: cannot create {target}: {exc}", file=sys.stderr)
    if created:
        print("created paths:")
        for path in created:
            print(f"  + {path}")
    else:
        print("all configured paths already exist")
    return 0


def _cmd_start(args: argparse.Namespace) -> int:
    transport = (os.environ.get("XNINETZY_MCP_TRANSPORT") or "stdio").strip().lower()
    if transport not in {"stdio", "streamable-http"}:
        print(
            f"XNINETZY_MCP_TRANSPORT must be stdio or streamable-http, got {transport!r}",
            file=sys.stderr,
        )
        return 2
    if transport == "streamable-http":
        print("authenticated_http_unavailable: use local stdio until owner HTTP authentication is implemented", file=sys.stderr)
        return 2
    cmd = [sys.executable, "-m", "xninetzy.interfaces.mcp_server"]
    print(f"starting MCP server (transport={transport})", file=sys.stderr)
    if args.dry_run:
        print("dry-run: would exec:", " ".join(cmd), file=sys.stderr)
        return 0
    try:
        return subprocess.call(cmd, env=os.environ)
    except KeyboardInterrupt:
        return 130


def _audit_payload() -> tuple[dict, list[str]]:
    proc = subprocess.run(
        [
            "uv",
            "run",
            "--no-project",
            "--directory",
            str(_REPO_ROOT),
            "python",
            str(_AUDIT_SCRIPT),
            "--json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode not in (0, 1) and not proc.stdout.strip():
        print(f"audit invocation failed: {proc.stderr.strip()}", file=sys.stderr)
        return {}, [f"audit invocation failed: rc={proc.returncode}"]
    import json

    try:
        snapshot = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        return {}, [f"audit JSON decode failed: {exc}"]
    failures = list(snapshot.get("failures") or [])
    return snapshot, failures


def _cmd_release_check(_args: argparse.Namespace) -> int:
    snapshot, failures = _audit_payload()
    if not snapshot:
        for fail in failures:
            print(f"  [FAIL   ] audit                 {fail}")
        return 2
    from xninetzy.tools.release_check import run_release_checks

    try:
        checks = run_release_checks()
    except Exception as exc:
        # Configuration/provider exception messages can contain private values.
        print(f"  [FAIL   ] release_checks         {type(exc).__name__}")
        print("\noverall: FAIL")
        return 2
    ok = True
    for check in checks:
        print(f"  [{check.status:<7}] {check.name:<22} {check.detail}")
        if check.status != "PASS":
            ok = False
    if failures:
        for fail in failures:
            print(f"  [FAIL   ] audit                 {fail}")
        ok = False
    print()
    print("overall:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def _cmd_orchestrator(args: argparse.Namespace) -> int:
    cmd = [sys.executable, "-m", "xninetzy.cli.orchestrator", *args.orch_args]
    return subprocess.call(cmd, env=os.environ)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="xninetzy-cli-supervisor")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init", help="create DATA_DIR, OUTPUT_DIR, Obsidian vault")
    start_p = sub.add_parser("start", help="start MCP server (stdio default)")
    start_p.add_argument(
        "--dry-run",
        action="store_true",
        help="print the command that would be exec'd, do not exec",
    )
    sub.add_parser("release-check", help="run mcp_audit.py and emit PASS/FAIL lines")
    orch_p = sub.add_parser(
        "orchestrator",
        help="pass through to xninetzy.cli.orchestrator",
    )
    orch_p.add_argument("orch_args", nargs=argparse.REMAINDER)
    parsed = parser.parse_args(argv)
    if parsed.command == "init":
        return _cmd_init(parsed)
    if parsed.command == "start":
        return _cmd_start(parsed)
    if parsed.command == "release-check":
        return _cmd_release_check(parsed)
    if parsed.command == "orchestrator":
        return _cmd_orchestrator(parsed)
    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
