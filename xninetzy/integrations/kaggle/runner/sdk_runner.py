from __future__ import annotations

import json
import signal
import sys
import tempfile
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

TEXT_LIMIT = 65_536
READ_CEILING = 1_048_576


def _api():
    from kaggle.api.kaggle_api_extended import KaggleApi

    client = KaggleApi()
    client.authenticate()
    return client


def _iso(value):
    if value is None:
        return None
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def _seconds(value):
    return int(value.total_seconds()) if hasattr(value, "total_seconds") else None


def _get(item, name):
    return getattr(item, name, None)


def _dataset_row(item):
    return {
        "ref": _get(item, "ref"),
        "title": _get(item, "title"),
        "subtitle": _get(item, "subtitle"),
        "total_bytes": _get(item, "total_bytes"),
        "last_updated": _iso(_get(item, "last_updated")),
        "download_count": _get(item, "download_count"),
        "vote_count": _get(item, "vote_count"),
        "usability_rating": _get(item, "usability_rating"),
        "license_name": _get(item, "license_name"),
        "is_private": _get(item, "is_private"),
        "url": _get(item, "url"),
    }


def _split(reference):
    owner, _, slug = str(reference).partition("/")
    return owner, slug


def _read_remote(url, limit):
    import requests

    response = requests.get(url, timeout=30, stream=True)
    response.raise_for_status()
    chunks = []
    size = 0
    for chunk in response.iter_content(chunk_size=8192):
        chunks.append(chunk)
        size += len(chunk)
        if size > limit:
            break
    response.close()
    data = b"".join(chunks)
    return {
        "text": data[:limit].decode("utf-8", "replace"),
        "truncated": len(data) > limit,
        "bytes": min(len(data), limit),
    }


def _repair(text):
    if not any("\x80" <= char <= "\xff" for char in text):
        return text
    try:
        return text.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text


def _plain_log(raw):
    text = raw or ""
    try:
        events = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return _repair(text)
    if not isinstance(events, list):
        return _repair(text)
    return _repair("".join(str(event.get("data", "")) for event in events if isinstance(event, dict)))


def _quota(item):
    if item is None:
        return None
    total = _seconds(_get(item, "total_time_allowed"))
    used = _seconds(_get(item, "time_used"))
    reserved = _seconds(_get(item, "time_reserved"))
    known = None not in (total, used, reserved)
    return {
        "total_seconds": total,
        "used_seconds": used,
        "reserved_seconds": reserved,
        "remaining_seconds": max(0, total - used - reserved) if known else None,
    }


def op_whoami(api, args):
    return {"username": api.get_config_value("username") or None}


def op_dataset_list(api, args):
    limit = max(1, min(int(args.get("limit", 25)), 50))
    rows = []
    for page in range(1, 4):
        items = api.dataset_list(search=args["query"], page=page) or []
        rows.extend(_dataset_row(item) for item in items)
        if not items or len(rows) >= limit:
            break
    return {"datasets": rows[:limit]}


def op_dataset_get(api, args):
    from kagglesdk.datasets.types.dataset_api_service import ApiGetDatasetRequest

    owner, slug = _split(args["ref"])
    request = ApiGetDatasetRequest()
    request.owner_slug = owner
    request.dataset_slug = slug
    with api.build_kaggle_client() as sdk:
        item = sdk.datasets.dataset_api_client.get_dataset(request)
    row = _dataset_row(item)
    row["current_version"] = _get(item, "current_version_number")
    return row


def op_dataset_files(api, args):
    limit = max(1, min(int(args.get("limit", 200)), 500))
    files = []
    token = None
    while True:
        response = api.dataset_list_files(args["ref"], page_token=token, page_size=min(200, limit))
        files.extend({"name": f.name, "total_bytes": f.total_bytes} for f in response.files or [])
        token = response.next_page_token or None
        if not token or len(files) >= limit:
            break
    return {"files": files[:limit], "has_more": bool(token)}


def op_dataset_download(api, args):
    target = Path(args["path"])
    target.mkdir(parents=True, exist_ok=True)
    api.dataset_download_files(
        args["ref"],
        path=str(target),
        force=bool(args.get("force", False)),
        quiet=True,
        unzip=True,
    )
    files = [
        {"name": str(path.relative_to(target)), "bytes": path.stat().st_size}
        for path in sorted(target.rglob("*"))
        if path.is_file()
    ]
    return {"path": str(target), "files": files}


def op_kernel_push(api, args):
    with tempfile.TemporaryDirectory(prefix="xn-kaggle-") as folder:
        root = Path(folder)
        (root / args["code_file"]).write_text(args["code"], encoding="utf-8")
        (root / "kernel-metadata.json").write_text(json.dumps(args["metadata"]), encoding="utf-8")
        result = api.kernels_push(str(root), timeout=args.get("timeout"), acc=args.get("accelerator"))
    invalid = {
        name: list(getattr(result, name) or [])
        for name in dir(result)
        if name.startswith("invalid_") and not callable(getattr(result, name, None))
    }
    return {
        "error": _get(result, "error") or None,
        "invalid": {name: values for name, values in invalid.items() if values},
        "url": _get(result, "url") or None,
        "version": _get(result, "version_number"),
    }


def op_kernel_status(api, args):
    response = api.kernels_status(args["kernel"])
    return {
        "status": getattr(response.status, "name", str(response.status)).upper(),
        "failure_message": response.failure_message or None,
    }


def op_kernel_presence(api, args):
    user = str(api.get_config_value("username") or "").strip()
    if not user:
        raise ValueError("authenticated Kaggle username is unavailable")
    requested = set(args.get("kernels") or [])
    witness = args.get("witness")
    if not witness or any(not ref.startswith(user + "/") for ref in requested | {witness}):
        raise ValueError("presence checks require same-account refs and a known witness")
    found, seen = set(), set()
    redacted = 0
    complete = False
    for page in range(1, 26):
        rows = api.kernels_list(mine=True, page=page, page_size=100)
        if not isinstance(rows, list):
            raise ValueError("owned-kernel listing did not return a list")
        for item in rows:
            ref = _get(item, "ref")
            if _redacted_row(item):
                redacted += 1
                continue
            if not isinstance(ref, str) or not ref.startswith(user + "/") or ref in seen:
                raise ValueError("owned-kernel listing is malformed or repeated")
            seen.add(ref)
            if ref in requested:
                found.add(ref)
        if len(rows) < 100:
            complete = True
            break
    return {"username": user, "complete": complete, "witness_present": witness in seen,
            "found": sorted(found), "scanned": len(seen), "redacted": redacted}


def _redacted_row(item):
    return (_get(item, "ref") == "" and _get(item, "id") in (0, None)
            and _get(item, "title") == "[Private Notebook]")


def op_kernel_output(api, args):
    from kagglesdk.kernels.types.kernels_api_service import ApiListKernelSessionOutputRequest

    owner, slug = _split(args["kernel"])
    request = ApiListKernelSessionOutputRequest()
    request.user_name = owner
    request.kernel_slug = slug
    request.page_size = 200
    if args.get("page_token"):
        request.page_token = args["page_token"]
    with api.build_kaggle_client() as sdk:
        response = sdk.kernels.kernels_api_client.list_kernel_session_output(request)
    files = list(response.files or [])
    limit = max(1, min(int(args.get("max_read_bytes", TEXT_LIMIT)), READ_CEILING))
    reads = {}
    for wanted in args.get("read") or []:
        match = next((f for f in files if f.file_name == wanted or Path(f.file_name).name == wanted), None)
        reads[wanted] = _read_remote(match.url, limit) if match is not None else None
    result = {
        "files": [f.file_name for f in files],
        "has_more": bool(response.next_page_token),
        "next_page_token": response.next_page_token or None,
        "reads": reads,
    }
    tail = max(0, min(int(args.get("log_tail_chars", 0)), 50_000))
    if tail:
        result["log_tail"] = _plain_log(response.log)[-tail:]
    return result


def op_kernel_logs(api, args):
    seconds = max(1, min(int(args.get("seconds", 20)), 60))
    tail = max(1, min(int(args.get("log_tail_chars", 4000)), 50_000))

    class Finished(BaseException):
        pass

    def expire(*_):
        raise Finished()

    collected = []
    size = 0
    stream = api.kernels_logs_stream(args["kernel"])
    if hasattr(signal, "SIGALRM"):
        signal.signal(signal.SIGALRM, expire)
        signal.alarm(seconds)
    try:
        for event in stream:
            value = event.get("data", "")
            if value.strip():
                collected.append(value[:2500])
                size += len(value)
            if size > tail * 4:
                break
    except Finished:
        pass
    finally:
        if hasattr(signal, "SIGALRM"):
            signal.alarm(0)
        stream.close()
    return {"log_tail": _repair("".join(collected))[-tail:]}


def op_quota(api, args):
    with api.build_kaggle_client() as sdk:
        stats = sdk.kernels.kernels_api_client.get_accelerator_quota_statistics()
    return {
        "gpu": _quota(_get(stats, "gpu_quota")),
        "tpu": _quota(_get(stats, "tpu_quota")),
        "refresh_time": _iso(_get(stats, "quota_refresh_time")),
    }


OPERATIONS = {
    "whoami": op_whoami,
    "dataset_list": op_dataset_list,
    "dataset_get": op_dataset_get,
    "dataset_files": op_dataset_files,
    "dataset_download": op_dataset_download,
    "kernel_push": op_kernel_push,
    "kernel_status": op_kernel_status,
    "kernel_presence": op_kernel_presence,
    "kernel_output": op_kernel_output,
    "kernel_logs": op_kernel_logs,
    "quota": op_quota,
}


def _failure(exc):
    return {
        "ok": False,
        "error": {
            "type": type(exc).__name__,
            "message": str(exc)[:500],
            "status_code": getattr(getattr(exc, "response", None), "status_code", None),
        },
    }


def execute(request, api_factory=_api):
    api = None
    auth_failure = None
    results = []
    for item in request.get("ops", []):
        handler = OPERATIONS.get(item.get("op"))
        if handler is None:
            results.append(_failure(ValueError("unknown operation " + str(item.get("op"))[:60])))
            continue
        if auth_failure is not None:
            results.append(auth_failure)
            continue
        try:
            if api is None:
                api = api_factory()
        except (Exception, SystemExit) as exc:
            auth_failure = _failure(exc)
            results.append(auth_failure)
            continue
        try:
            results.append({"ok": True, "data": handler(api, item.get("args") or {})})
        except Exception as exc:
            results.append(_failure(exc))
    return {"results": results}


def main():
    request = json.loads(sys.stdin.read() or "{}")
    sys.stdout.write("\n" + json.dumps(execute(request), default=str) + "\n")
    sys.stdout.flush()


if __name__ == "__main__":
    main()
