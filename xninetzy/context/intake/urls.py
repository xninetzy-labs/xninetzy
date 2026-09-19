from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit


URL_KIND_GITHUB: str = "github"
URL_KIND_RAW_GITHUB: str = "raw_github"
URL_KIND_LOCAL: str = "local"
URL_KIND_UNKNOWN: str = "unknown"


_GITHUB_HOST_RE = re.compile(r"(?:^|\.)github\.io$", re.IGNORECASE)
_GITHUB_BLOB_RE = re.compile(r"^/([^/]+)/([^/]+)/blob/([^/]+)/(.*)$")
_GITHUB_TREE_RE = re.compile(r"^/([^/]+)/([^/]+)/tree/([^/]+)(?:/(.*))?$")
_GITHUB_RAW_RE = re.compile(r"^/([^/]+)/([^/@]+)(?:@([^/]+))?/(.+)$")


def _split_raw_path(path: str) -> tuple[str, str, str | None, str | None]:
    segments = [seg for seg in path.split("/") if seg]
    if len(segments) < 3:
        raise ValueError(f"raw URL needs owner/repo/ref/file: {path!r}")
    owner = segments[0]
    repo_with_ref = segments[1]
    if "@" in repo_with_ref:
        repo, _, ref = repo_with_ref.partition("@")
        subpath = "/".join(segments[2:])
        return owner, repo, ref, subpath or None
    repo = repo_with_ref
    ref = segments[2]
    subpath = "/".join(segments[3:])
    return owner, repo, ref, subpath or None


@dataclass(frozen=True, slots=True)
class URLKind:
    name: str
    raw: str
    canonical: str | None = None
    owner: str | None = None
    repo: str | None = None
    ref: str | None = None
    subpath: str | None = None
    host: str | None = None


def sha256_hex(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _strip_query_fragment(url: str) -> str:
    parts = urlsplit(url)
    return parts._replace(query="", fragment="").geturl()


def _normalize_host(host: str) -> str:
    return host.lower().strip()


def detect_url_kind(raw: str) -> str:
    candidate = (raw or "").strip()
    if not candidate:
        return URL_KIND_UNKNOWN
    if candidate.startswith("file://"):
        return URL_KIND_LOCAL
    if candidate.startswith("/") or candidate.startswith("./") or candidate.startswith("../"):
        return URL_KIND_LOCAL
    try:
        parts = urlsplit(candidate)
    except ValueError:
        return URL_KIND_UNKNOWN
    if parts.scheme and parts.scheme not in ("http", "https"):
        return URL_KIND_UNKNOWN
    host = _normalize_host(parts.netloc)
    if not host:
        return URL_KIND_LOCAL if Path(candidate).expanduser().exists() else URL_KIND_UNKNOWN
    if host in ("github.com", "www.github.com"):
        return URL_KIND_GITHUB
    if host == "raw.githubusercontent.com":
        return URL_KIND_RAW_GITHUB
    if _GITHUB_HOST_RE.search(host):
        return URL_KIND_GITHUB
    return URL_KIND_UNKNOWN


def parse_github_url(url: str) -> URLKind:
    cleaned = _strip_query_fragment((url or "").strip())
    parts = urlsplit(cleaned)
    host = _normalize_host(parts.netloc)
    if host not in ("github.com", "www.github.com"):
        raise ValueError(f"not a github URL: {url!r}")
    path = parts.path or ""
    blob = _GITHUB_BLOB_RE.match(path)
    if blob:
        owner, repo, ref, subpath = blob.groups()
        canonical = f"https://github.com/{owner}/{repo}"
        return URLKind(
            name=URL_KIND_GITHUB,
            raw=cleaned,
            canonical=canonical,
            owner=owner,
            repo=repo,
            ref=ref,
            subpath=subpath,
            host=host,
        )
    tree = _GITHUB_TREE_RE.match(path)
    if tree:
        owner, repo, ref, subpath = tree.groups()
        canonical = f"https://github.com/{owner}/{repo}"
        return URLKind(
            name=URL_KIND_GITHUB,
            raw=cleaned,
            canonical=canonical,
            owner=owner,
            repo=repo,
            ref=ref,
            subpath=subpath or None,
            host=host,
        )
    segments = [seg for seg in path.split("/") if seg]
    if len(segments) >= 2:
        owner, repo = segments[0], segments[1]
        if repo.endswith(".git"):
            repo = repo[:-4]
        canonical = f"https://github.com/{owner}/{repo}"
        return URLKind(
            name=URL_KIND_GITHUB,
            raw=cleaned,
            canonical=canonical,
            owner=owner,
            repo=repo,
            ref=None,
            subpath=None,
            host=host,
        )
    raise ValueError(f"unrecognised github URL path: {url!r}")


def parse_raw_github_url(url: str) -> URLKind:
    cleaned = _strip_query_fragment((url or "").strip())
    parts = urlsplit(cleaned)
    host = _normalize_host(parts.netloc)
    if host != "raw.githubusercontent.com":
        raise ValueError(f"not a raw.githubusercontent.com URL: {url!r}")
    owner, repo, ref, subpath = _split_raw_path(parts.path or "")
    canonical = f"https://github.com/{owner}/{repo}"
    return URLKind(
        name=URL_KIND_RAW_GITHUB,
        raw=cleaned,
        canonical=canonical,
        owner=owner,
        repo=repo,
        ref=ref,
        subpath=subpath,
        host=host,
    )


def parse_local_path(raw: str) -> URLKind:
    candidate = (raw or "").strip()
    if candidate.startswith("file://"):
        cleaned = urlsplit(candidate).path or ""
    else:
        cleaned = candidate
    expanded = Path(cleaned).expanduser()
    canonical = str(expanded.resolve(strict=False)) if expanded.exists() or expanded.parent.exists() else cleaned
    return URLKind(
        name=URL_KIND_LOCAL,
        raw=candidate,
        canonical=canonical,
        owner=None,
        repo=expanded.name or None,
        ref=None,
        subpath=None,
        host=None,
    )


def canonicalize_github_url(url: URLKind) -> str:
    if url.canonical:
        return url.canonical
    return url.raw


def parse_url(raw: str) -> URLKind:
    kind = detect_url_kind(raw)
    if kind == URL_KIND_GITHUB:
        return parse_github_url(raw)
    if kind == URL_KIND_RAW_GITHUB:
        return parse_raw_github_url(raw)
    if kind == URL_KIND_LOCAL:
        return parse_local_path(raw)
    raise ValueError(f"unsupported URL kind for raw={raw!r}: {kind}")
