from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _fetch_proposals(status: str, limit: int) -> list[dict[str, object]]:
    from xninetzy.db.migrations import run_migrations
    from xninetzy.db.sqlite import connect

    run_migrations()
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM improvement_proposals WHERE status=? ORDER BY id DESC LIMIT ?",
            (status, max(1, limit)),
        ).fetchall()
    return [dict(row) for row in rows]


def _risk_for(proposal: dict[str, object]) -> str:
    raw = proposal.get("metadata_json")
    if not raw:
        return "unknown"
    try:
        payload = json.loads(str(raw))
    except (TypeError, json.JSONDecodeError):
        return "unknown"
    return str(
        payload.get("risk")
        or payload.get("tier")
        or proposal.get("risk_level")
        or "unknown"
    ).strip().lower() or "unknown"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Dry-run listing of tier<=1 improvement proposals.")
    parser.add_argument("--status", default="proposed", help="Filter by proposal status (default: proposed).")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--output", default=None)
    args = parser.parse_args(argv)

    proposals = _fetch_proposals(args.status, args.limit)
    auto_eligible: list[dict[str, object]] = []
    needs_review: list[dict[str, object]] = []
    for proposal in proposals:
        risk = _risk_for(proposal)
        item = {
            "id": proposal.get("id"),
            "title": proposal.get("title"),
            "problem": proposal.get("problem"),
            "owner": proposal.get("owner"),
            "created_at": proposal.get("created_at"),
            "risk_level": proposal.get("risk_level"),
            "risk": risk,
        }
        if risk in {"read", "write", "draft", "tier_0", "tier_1", "0", "1"}:
            item["verdict"] = "dry_run_eligible"
            auto_eligible.append(item)
        else:
            item["verdict"] = "requires_owner_approval"
            needs_review.append(item)
    report = {
        "generated_at": _now_iso(),
        "status_filter": args.status,
        "fetched": len(proposals),
        "dry_run_eligible": auto_eligible,
        "requires_owner_approval": needs_review,
        "note": "dry-run only; no source modification. Use improvement_approve to apply.",
    }
    if args.output:
        output_path = Path(args.output)
    else:
        output_dir = REPO_ROOT / "generated" / "untracked"
        output_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        output_path = output_dir / f"improvement-applier-{stamp}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    summary = json.dumps(
        {
            "fetched": len(proposals),
            "dry_run_eligible": len(auto_eligible),
            "requires_owner_approval": len(needs_review),
            "report": str(output_path),
        },
        ensure_ascii=False,
    )
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
