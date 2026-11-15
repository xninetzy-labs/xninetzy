"""Control only: source upload, status and small JSON/log reads; no report downloads."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OWNER = "misbahulmuttaqin"


def api():
    from kaggle.api.kaggle_api_extended import KaggleApi
    client = KaggleApi()
    client.authenticate()
    return client


def build(slug, job, sources=(), gpu=False):
    target = ROOT / "jobs" / slug
    target.mkdir(parents=True, exist_ok=True)
    source = "JOB = " + repr(job) + "\n" + (ROOT / "remote_worker.py").read_text()
    (target / "worker.py").write_text(source)
    metadata = {"id": OWNER + "/" + slug, "title": slug.replace("-", " ").title(), "code_file": "worker.py", "language": "python", "kernel_type": "script", "is_private": True, "enable_gpu": gpu, "enable_internet": True, "dataset_sources": [], "competition_sources": [], "kernel_sources": list(sources), "model_sources": []}
    (target / "kernel-metadata.json").write_text(json.dumps(metadata, indent=2))
    return target


def push(slug, job, sources=(), gpu=False):
    target = build(slug, job, sources, gpu)
    result = api().kernels_push(str(target), timeout=str(job.get("time_budget_seconds", 25_200) + 240), acc=job.get("accelerator", "NvidiaTeslaT4") if gpu else None)
    if result.error or result.invalid_kernel_sources or result.invalid_dataset_sources:
        raise RuntimeError("Kaggle did not accept the requested job or its sources: " + (result.error or "invalid input sources"))
    receipt = {"slug": OWNER + "/" + slug, "url": result.url, "version": result.version_number}
    print(json.dumps(receipt, default=str), flush=True)
    return receipt


def output_response(slug):
    from kagglesdk.kernels.types.kernels_api_service import ApiListKernelSessionOutputRequest
    client = api()
    request = ApiListKernelSessionOutputRequest()
    request.user_name = OWNER
    request.kernel_slug = slug
    request.page_size = 200
    with client.build_kaggle_client() as sdk:
        return sdk.kernels.kernels_api_client.list_kernel_session_output(request)


def read_status_json(response, name="summary.json"):
    import requests
    if name not in {"summary.json", "fatal.json"}:
        raise RuntimeError("Local reads are limited to execution status, never reports/text/Excel")
    for item in response.files or []:
        if Path(item.file_name).name == name:
            result = requests.get(item.url, timeout=30, stream=True)
            result.raise_for_status()
            data = result.raw.read(65537)
            result.close()
            if len(data) > 65536:
                raise RuntimeError("Execution status exceeds limit")
            return json.loads(data)
    return None


def inspect_output(slug, names):
    response = output_response(slug)
    print(json.dumps({"outputs": [f.file_name for f in response.files or []], "next_page": bool(response.next_page_token)}))
    for item in response.files or []:
        if Path(item.file_name).name in names:
            print(json.dumps({"file": item.file_name, "status": read_status_json(response, Path(item.file_name).name)}))
    if response.log:
        # Worker only logs progress/diagnostics, never extracted document text.
        print(response.log[-14000:])


def save_state(state):
    target = ROOT / "campaign_state.json"
    temporary = target.with_suffix(".tmp")
    temporary.write_text(json.dumps(state, indent=2))
    temporary.replace(target)


def live_logs(slug):
    import signal

    class ObservationFinished(BaseException):
        pass

    def timeout(*args):
        raise ObservationFinished()

    signal.signal(signal.SIGALRM, timeout)
    signal.alarm(20)
    stream = api().kernels_logs_stream(OWNER + "/" + slug)
    try:
        for event in stream:
            value = event.get("data", "")
            if value.strip():
                print(value[:2500], end="" if value.endswith("\n") else "\n", flush=True)
    except ObservationFinished:
        pass
    finally:
        signal.alarm(0)
        stream.close()


def initialize_campaign(inventory_slug):
    if (ROOT / "campaign_state.json").exists():
        raise RuntimeError("Campaign already initialized; use tick to resume")
    summary = read_status_json(output_response(inventory_slug))
    if not summary or not summary.get("complete"):
        raise RuntimeError("A verified complete Kaggle inventory is required")
    seeds = json.loads((ROOT / "seeds.json").read_text())
    jobs = []
    for index, seed in enumerate(seeds):
        count = summary["roots"].get(seed["id"], 0)
        if count == 0:
            continue
        tag = f"{index+1:02d}"
        download = "biodiversity-download-" + tag
        extract = "biodiversity-extract-" + tag
        jobs.append({"slug": download, "mode": "download", "root": seed["id"], "sector": seed["sector"], "expected": count, "sources": [inventory_slug], "depends": [], "state": "pending", "gpu": False})
        jobs.append({"slug": extract, "mode": "extract", "sector": seed["sector"], "expected": count, "sources": [download], "depends": [download], "state": "pending", "gpu": True})
    sector_merges = []
    for index, sector in enumerate(dict.fromkeys(s["sector"] for s in seeds)):
        children = [j for j in jobs if j["mode"] == "extract" and j["sector"] == sector]
        slug = f"biodiversity-sector-{index+1:02d}"
        jobs.append({"slug": slug, "mode": "merge", "expected": sum(j["expected"] for j in children), "sources": [j["slug"] for j in children], "depends": [j["slug"] for j in children], "state": "pending", "gpu": False})
        sector_merges.append(slug)
    jobs.append({"slug": "biodiversity-final-excel", "mode": "merge", "expected": summary["files"], "sources": sector_merges, "depends": sector_merges, "state": "pending", "gpu": False})
    state = {"inventory": inventory_slug, "expected_files": summary["files"], "created": time.time(), "jobs": jobs}
    save_state(state)
    print(json.dumps({"campaign_jobs": len(jobs), "expected_files": summary["files"]}))


def campaign_tick():
    state = json.loads((ROOT / "campaign_state.json").read_text())
    client = api()
    if not state.get("smoke_verified"):
        proof = read_status_json(output_response("biodiversity-pipeline-cpu-smoke"))
        state["smoke_verified"] = bool(proof and proof.get("complete") and proof.get("mode") == "smoke")
        save_state(state)
    by_slug = {j["slug"]: j for j in state["jobs"]}
    for job in state["jobs"]:
        if job["state"] not in {"submitted", "submitting"}:
            continue
        run_slug = job.get("run_slug", job["slug"])
        response = client.kernels_status(OWNER + "/" + run_slug)
        status = getattr(response.status, "name", str(response.status)).upper()
        job["remote_status"] = status
        if status == "COMPLETE":
            summary = read_status_json(output_response(run_slug))
            job["summary"] = summary
            if summary and summary.get("complete"):
                job["state"] = "complete"
            elif summary and job["mode"] in {"download", "extract"}:
                if summary.get("deferred"):
                    state["download_not_before"] = time.time() + summary["deferred"].get("retry_after_seconds", 1800)
                metric = summary.get("downloaded", 0) if job["mode"] == "download" else summary.get("pages_processed", 0)
                stalled = job.get("stalled", 0) + 1 if metric <= job.get("last_progress", -1) else 0
                job["stalled"], job["last_progress"] = stalled, metric
                attempt = job.get("attempt", 1)
                if stalled < 2 and attempt < 16:
                    job["previous_sources"] = [run_slug]
                    job["attempt"] = attempt + 1
                    job["run_slug"] = job["slug"] + "-r" + str(attempt + 1)
                    job["state"] = "pending"
                    job["gpu"] = False  # Continuations remain eligible when GPU quota is gone.
                else:
                    job["state"] = "review_required" if summary.get("processed") == summary.get("expected") else "partial"
            elif summary and job["mode"] == "merge" and summary.get("files") == job["expected"]:
                job["state"] = "review_required"
            else:
                job["state"] = "partial"
        elif status in {"ERROR", "CANCELLED", "CANCELED"}:
            job["state"] = "failed"
            job["failure"] = response.failure_message
        save_state(state)
    active_cpu = sum(j["state"] in {"submitted", "submitting"} and not j["gpu"] for j in state["jobs"])
    active_gpu = sum(j["state"] in {"submitted", "submitting"} and j["gpu"] for j in state["jobs"])
    active_cpu_extract = sum(j["state"] in {"submitted", "submitting"} and not j["gpu"] and j["mode"] == "extract" for j in state["jobs"])
    remaining_gpu = 0
    try:
        with client.build_kaggle_client() as sdk:
            quota = sdk.kernels.kernels_api_client.get_accelerator_quota_statistics().gpu_quota
        remaining_gpu = max(0, int((quota.total_time_allowed - quota.time_used - quota.time_reserved).total_seconds()))
    except Exception:
        pass  # An unknown quota never authorizes a GPU reservation.
    for job in state["jobs"]:
        if job["state"] != "pending" or not all(by_slug[s]["state"] in {"complete", "review_required"} for s in job["depends"]):
            continue
        if job["mode"] == "extract" and not state.get("smoke_verified"):
            continue
        if job["mode"] == "download" and time.time() < state.get("download_not_before", 0):
            continue
        use_gpu = bool(job["gpu"] and remaining_gpu >= 900 and active_gpu < 2)
        if not use_gpu and active_cpu >= 4:
            continue
        if not use_gpu and job["mode"] == "extract" and active_cpu_extract >= 2 and any(j["mode"] == "download" and j["state"] == "pending" for j in state["jobs"]):
            continue  # Keep one CPU slot available for acquisition.
        job["gpu"] = use_gpu
        job["state"] = "submitting"
        save_state(state)  # An uncertain push is reconciled, never blindly replayed.
        reservation = min(1800, remaining_gpu - 60) if use_gpu else 25_440
        config = {"mode": job["mode"], "time_budget_seconds": reservation - 240}
        if job["mode"] == "download":
            config["root"] = job["root"]
        if job["mode"] == "merge":
            config["expected_files"] = job["expected"]
        sources = [by_slug[s].get("run_slug", s) if s in by_slug else s for s in job["sources"]]
        sources += job.get("previous_sources", [])
        receipt = push(job.get("run_slug", job["slug"]), config, [OWNER + "/" + s for s in sources], use_gpu)
        job["receipt"] = receipt
        job["state"] = "submitted"
        save_state(state)
        active_gpu += int(job["gpu"])
        active_cpu += int(not job["gpu"])
        active_cpu_extract += int(not job["gpu"] and job["mode"] == "extract")
        remaining_gpu -= reservation if use_gpu else 0
    print(json.dumps({"states": {s: sum(j["state"] == s for j in state["jobs"]) for s in sorted({j["state"] for j in state["jobs"]})}, "downloaded_files": sum(j.get("summary", {}).get("downloaded", 0) for j in state["jobs"] if j["mode"] == "download"), "scored_pdfs": sum(j.get("summary", {}).get("complete_pdfs", 0) for j in state["jobs"] if j["mode"] == "extract")}))


def supervise():
    import fcntl
    import traceback

    failures = 0
    with (ROOT / "campaign.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        lock.write(str(__import__("os").getpid()))
        lock.flush()
        while True:
            try:
                campaign_tick()
                failures = 0
                state = json.loads((ROOT / "campaign_state.json").read_text())
                jobs = state["jobs"]
                if all(j["state"] in {"complete", "review_required"} for j in jobs):
                    print(json.dumps({"campaign": "complete" if all(j["state"] == "complete" for j in jobs) else "review_required", "final_url": "https://www.kaggle.com/code/" + OWNER + "/biodiversity-final-excel"}), flush=True)
                    return
                active = any(j["state"] in {"submitted", "submitting"} for j in jobs)
                by_slug = {j["slug"]: j for j in jobs}
                ready = any(j["state"] == "pending" and all(by_slug[s]["state"] in {"complete", "review_required"} for s in j["depends"]) for j in jobs)
                if not active and not ready:
                    print(json.dumps({"campaign": "needs_diagnosis", "jobs": [{"slug": j["slug"], "state": j["state"]} for j in jobs if j["state"] in {"failed", "partial", "submitting"}]}), flush=True)
                    return
            except Exception as exc:
                failures += 1
                print(json.dumps({"control_error": type(exc).__name__, "consecutive": failures, "detail": str(exc)[:300]}), flush=True)
                if failures >= 10:
                    traceback.print_exc()
                    raise
            time.sleep(45 if not failures else min(60, failures * 15))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["smoke", "inventory", "inspect", "status", "download", "extract", "merge", "campaign-init", "tick", "live", "supervise"])
    parser.add_argument("slug")
    parser.add_argument("--root")
    parser.add_argument("--source", action="append", default=[])
    parser.add_argument("--expected", type=int)
    args = parser.parse_args()
    if args.action == "supervise":
        supervise()
    elif args.action == "live":
        live_logs(args.slug)
    elif args.action == "campaign-init":
        initialize_campaign(args.slug)
    elif args.action == "tick":
        campaign_tick()
    elif args.action == "status":
        result = api().kernels_status(OWNER + "/" + args.slug)
        print(result)
    elif args.action == "inspect":
        inspect_output(args.slug, {"summary.json", "fatal.json"})
    else:
        job = {"mode": args.action, "time_budget_seconds": 25_200}
        if args.action == "inventory":
            job["seeds"] = json.loads((ROOT / "seeds.json").read_text())
        if args.action == "download":
            job["root"] = args.root
        if args.action == "merge":
            job["expected_files"] = args.expected
        push(args.slug, job, args.source, gpu=args.action in ("smoke", "extract"))
