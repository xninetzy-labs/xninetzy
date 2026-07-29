from __future__ import annotations

import argparse
import asyncio
import json

from app.xninetzy.os.web_analysis.analyzer_service import AnalyzerService
from app.xninetzy.os.web_analysis.cache_manager import AnalysisCacheManager
from app.xninetzy.os.web_analysis.manual_login import capture_manual_session
from app.xninetzy.os.web_analysis.session_manager import SessionManager


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Xninetzy read-only web analysis utility")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze = subparsers.add_parser("analyze", help="Analyze allowlisted site structure")
    analyze.add_argument("--site", required=True, choices=("hebat", "mahasiswa"))
    analyze.add_argument("--authenticated", action="store_true", help="Use the local owner's encrypted session")
    analyze.add_argument("--profile", help="Override the configured local profile ID")
    analyze.add_argument("--force", action="store_true")

    login = subparsers.add_parser("login", help="Capture a manual headed-browser session")
    login.add_argument("--site", required=True, choices=("hebat", "mahasiswa"))
    login.add_argument("--profile", help="Override the configured local profile ID")
    login.add_argument("--credential-source", choices=("hebat",))

    status = subparsers.add_parser("status", help="Show cache/session presence without secrets")
    status.add_argument("--site", required=True, choices=("hebat", "mahasiswa"))
    status.add_argument("--profile", help="Override the configured local profile ID")
    return parser


async def _run(args: argparse.Namespace) -> dict:
    if args.command == "analyze":
        result = await AnalyzerService().analyze_site(
            args.site,
            authenticated=args.authenticated,
            profile_id=args.profile,
            force=args.force,
        )
        return result.model_dump()
    if args.command == "login":
        return await capture_manual_session(
            args.site, args.profile, args.credential_source
        )

    cache = AnalysisCacheManager().load(args.site)
    result = {
        "site": args.site,
        "analysis_cached": cache is not None,
        "analysis_status": cache.auth_status if cache else None,
        "session_present": False,
    }
    try:
        result["session_present"] = SessionManager().has_session(args.site, args.profile)
    except Exception as exc:
        result["session_error"] = str(exc)
    return result


def main() -> None:
    args = build_parser().parse_args()
    print(json.dumps(asyncio.run(_run(args)), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
