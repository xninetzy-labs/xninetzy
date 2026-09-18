from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _run_step(label: str, command: list[str], cwd: Path) -> dict[str, object]:
    started_at = _now_iso()
    started = time.monotonic()
    try:
        result = subprocess.run(
            command,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=900,
            check=False,
        )
        elapsed = time.monotonic() - started
        return {
            "label": label,
            "command": command,
            "cwd": str(cwd),
            "started_at": started_at,
            "finished_at": _now_iso(),
            "elapsed_seconds": round(elapsed, 2),
            "exit_code": result.returncode,
            "stdout_tail": "\n".join(result.stdout.splitlines()[-30:]),
            "stderr_tail": "\n".join(result.stderr.splitlines()[-30:]),
            "status": "ok" if result.returncode == 0 else "failed",
        }
    except subprocess.TimeoutExpired:
        elapsed = time.monotonic() - started
        return {
            "label": label,
            "command": command,
            "cwd": str(cwd),
            "started_at": started_at,
            "finished_at": _now_iso(),
            "elapsed_seconds": round(elapsed, 2),
            "exit_code": -1,
            "stdout_tail": "",
            "stderr_tail": "timeout after 900s",
            "status": "timeout",
        }
    except Exception as exc:
        elapsed = time.monotonic() - started
        return {
            "label": label,
            "command": command,
            "cwd": str(cwd),
            "started_at": started_at,
            "finished_at": _now_iso(),
            "elapsed_seconds": round(elapsed, 2),
            "exit_code": -1,
            "stdout_tail": "",
            "stderr_tail": str(exc),
            "status": "error",
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run lint+test+verify+yarn and emit a JSON report.")
    parser.add_argument("--output", default=None, help="Override report output path.")
    parser.add_argument("--skip-yarn", action="store_true", help="Skip apps/docs yarn check+build.")
    parser.add_argument("--skip-verify", action="store_true", help="Skip scripts/verify_cpu_only.py.")
    parser.add_argument("--keep-going", action="store_true", help="Continue on failure (default: stop).")
    args = parser.parse_args(argv)

    steps: list[dict[str, object]] = []
    plan = [
        ("ruff", ["uv", "run", "ruff", "check", "xninetzy", "tests"], REPO_ROOT),
        ("pytest", ["uv", "run", "pytest", "-ra", "-q"], REPO_ROOT),
    ]
    if not args.skip_verify:
        plan.append(
            (
                "verify_cpu_only",
                ["uv", "run", "python", "scripts/verify_cpu_only.py"],
                REPO_ROOT,
            )
        )
    if not args.skip_yarn:
        docs_dir = REPO_ROOT / "apps" / "docs"
        plan.append(("yarn_check", ["yarn", "check"], docs_dir))
        plan.append(("yarn_build", ["yarn", "build"], docs_dir))

    for label, command, cwd in plan:
        step = _run_step(label, command, cwd)
        steps.append(step)
        if step["status"] != "ok" and not args.keep_going:
            break

    overall_status = "ok" if all(step["status"] == "ok" for step in steps) else "failed"
    report = {
        "generated_at": _now_iso(),
        "repo_root": str(REPO_ROOT),
        "overall_status": overall_status,
        "step_count": len(steps),
        "steps": steps,
    }
    if args.output:
        output_path = Path(args.output)
    else:
        output_dir = REPO_ROOT / "generated" / "untracked"
        output_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        output_path = output_dir / f"optimize-report-{stamp}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    summary = json.dumps(
        {
            "status": overall_status,
            "report": str(output_path),
            "step_status": [step["status"] for step in steps],
        },
        ensure_ascii=False,
    )
    print(summary)
    return 0 if overall_status == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
