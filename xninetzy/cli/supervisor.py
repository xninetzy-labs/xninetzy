from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

from xninetzy.core.config import get_settings


_HOME = Path.home()
_DEFAULT_DATA = _HOME / ".local" / "share" / "xninetzy"
_DEFAULT_OUTPUT = _HOME / "Documents" / "xninetzy" / "output"
_DEFAULT_VAULT_HOST = _HOME / "Documents" / "xninetzy-vault"


def _env_or(value: str, default: Path) -> Path:
    raw = os.environ.get(value)
    if not raw:
        return default
    return Path(raw).expanduser()


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _check_python() -> tuple[str, str]:
    major, minor = sys.version_info[:2]
    return f"{major}.{minor}", "OK" if (major, minor) >= (3, 11) else "FAIL"


def _check_uv() -> str:
    return shutil.which("uv") and "OK" or "MISSING"


def _check_docker() -> str:
    return shutil.which("docker") and "OK" or "MISSING"


def _check_tesseract() -> str:
    return shutil.which("tesseract") and "OK" or "MISSING"


def cmd_init(args: argparse.Namespace) -> int:
    get_settings.cache_clear()
    data_dir = _env_or("DATA_DIR", _DEFAULT_DATA)
    output_dir = _env_or("OUTPUT_DIR", _DEFAULT_OUTPUT)
    vault_dir = _env_or("OBSIDIAN_VAULT_HOST_PATH", _DEFAULT_VAULT_HOST)

    print("Xninetzy init")
    print(f"  python        : {_check_python()[0]} ({_check_python()[1]})")
    print(f"  uv            : {_check_uv()}")
    print(f"  docker        : {_check_docker()}  (optional; only needed for self-hosted)")
    print(f"  tesseract     : {_check_tesseract()}  (optional; for OCR)")
    print()
    for path, label in [
        (data_dir, "DATA_DIR"),
        (output_dir, "OUTPUT_DIR"),
        (vault_dir, "OBSIDIAN_VAULT_HOST_PATH"),
    ]:
        _ensure_dir(path)
        print(f"  created {label:<28} {path}")
    print()
    print("next: xninetzy start")
    return 0


def cmd_start(args: argparse.Namespace) -> int:
    settings = get_settings()
    transport = (settings.XNINETZY_MCP_TRANSPORT or "stdio").strip().lower()
    host = settings.XNINETZY_MCP_HTTP_HOST
    port = int(settings.XNINETZY_MCP_HTTP_PORT)
    print(f"Xninetzy supervisor starting (transport={transport})")
    if transport == "streamable-http":
        print(f"  Streamable HTTP listener on http://{host}:{port}/mcp")
        print("  (stdio NOT started; ensure an MCP client connects via HTTP)")
    else:
        print("  stdio MCP listener (primary transport)")
    from xninetzy.interfaces.mcp_server import main as run_mcp_server
    try:
        run_mcp_server()
    except KeyboardInterrupt:
        print("\nSupervisor shutting down.")
    return 0


def cmd_release_check(args: argparse.Namespace) -> int:
    from xninetzy.tools.release_check import run_release_checks
    results = run_release_checks()
    overall = "PASS"
    for result in results:
        line = f"  [{result.status:<7}] {result.name:<24} {result.detail}"
        print(line)
        if result.status == "BLOCKED":
            overall = "BLOCKED"
        elif result.status == "WARN" and overall != "BLOCKED":
            overall = "WARN"
    print(f"\noverall: {overall}")
    return 0 if overall == "PASS" else (1 if overall == "WARN" else 2)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="xninetzy")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init", help="set up local directories + check prerequisites").set_defaults(func=cmd_init)
    sub.add_parser("start", help="run the MCP server").set_defaults(func=cmd_start)
    sub.add_parser("release-check", help="run release-gate checks").set_defaults(func=cmd_release_check)
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
