from __future__ import annotations

import re
import socket
from collections import Counter
from typing import Any, Callable
from urllib.parse import unquote, urlparse

ALLOWED_COMMANDS = frozenset({"PING", "INFO", "CONFIG", "SCAN", "TTL", "PTTL", "MEMORY", "TYPE", "SELECT", "AUTH", "DBSIZE"})
ALLOWED_SUBCOMMANDS: dict[str, frozenset[str]] = {"CONFIG": frozenset({"GET"}), "MEMORY": frozenset({"USAGE"})}
BIG_KEY_BYTES = 1024 * 1024
DEFAULT_SAMPLE = 500
MAX_SAMPLE = 5000
_BROKER_KEY = re.compile(r"^(?:celery|_kombu|unacked|celery-task-meta)", re.IGNORECASE)


class RedisError(RuntimeError):
    pass


class ReadOnlyViolation(RuntimeError):
    pass


def parse_redis_url(url: str) -> tuple[str, int, str, int]:
    parsed = urlparse(url)
    if parsed.scheme not in {"redis", "rediss"}:
        raise ValueError("url harus redis://")
    if parsed.scheme == "rediss":
        raise ValueError("rediss:// belum didukung")
    db = int(parsed.path.lstrip("/") or 0)
    return parsed.hostname or "localhost", parsed.port or 6379, unquote(parsed.password or ""), db


def _encode(args: tuple[Any, ...]) -> bytes:
    parts = [f"*{len(args)}\r\n".encode()]
    for arg in args:
        data = str(arg).encode()
        parts.append(f"${len(data)}\r\n".encode() + data + b"\r\n")
    return b"".join(parts)


class RedisReadOnly:
    def __init__(self, host: str, port: int, password: str = "", timeout: float = 5.0,
                 connect: Callable[..., Any] = socket.create_connection) -> None:
        self._sock = connect((host, port), timeout=timeout)
        self._buffer = b""
        if password:
            self.command("AUTH", password)

    def close(self) -> None:
        try:
            self._sock.close()
        except OSError:
            pass

    def _readline(self) -> bytes:
        while b"\r\n" not in self._buffer:
            chunk = self._sock.recv(65536)
            if not chunk:
                raise RedisError("koneksi ditutup")
            self._buffer += chunk
        line, _, self._buffer = self._buffer.partition(b"\r\n")
        return line

    def _readn(self, size: int) -> bytes:
        while len(self._buffer) < size + 2:
            chunk = self._sock.recv(65536)
            if not chunk:
                raise RedisError("koneksi ditutup")
            self._buffer += chunk
        data, self._buffer = self._buffer[:size], self._buffer[size + 2:]
        return data

    def _parse(self) -> Any:
        line = self._readline()
        kind, body = line[:1], line[1:]
        if kind == b"+":
            return body.decode()
        if kind == b"-":
            raise RedisError(body.decode(errors="replace")[:200])
        if kind == b":":
            return int(body)
        if kind == b"$":
            size = int(body)
            return None if size < 0 else self._readn(size).decode(errors="replace")
        if kind == b"*":
            count = int(body)
            return None if count < 0 else [self._parse() for _ in range(count)]
        raise RedisError("respons tidak dikenali")

    def command(self, *args: Any) -> Any:
        name = str(args[0]).upper()
        if name not in ALLOWED_COMMANDS:
            raise ReadOnlyViolation(f"perintah tidak diizinkan: {name}")
        allowed = ALLOWED_SUBCOMMANDS.get(name)
        if allowed and (len(args) < 2 or str(args[1]).upper() not in allowed):
            raise ReadOnlyViolation(f"subperintah tidak diizinkan: {name}")
        self._sock.sendall(_encode(args))
        return self._parse()


def parse_info(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in (text or "").splitlines():
        if line and not line.startswith("#") and ":" in line:
            key, _, value = line.partition(":")
            values[key.strip()] = value.strip()
    return values


def _config(client: RedisReadOnly, name: str) -> str:
    reply = client.command("CONFIG", "GET", name) or []
    return str(reply[1]) if len(reply) >= 2 else ""


def _finding(rule: str, severity: str, message: str, remediation: str) -> dict[str, str]:
    return {"id": rule, "severity": severity, "message": message, "remediation": remediation}


def _scan_sample(client: RedisReadOnly, limit: int) -> list[str]:
    keys: list[str] = []
    cursor = "0"
    while len(keys) < limit:
        reply = client.command("SCAN", cursor, "COUNT", 200)
        cursor, batch = str(reply[0]), reply[1] or []
        keys.extend(str(k) for k in batch)
        if cursor == "0":
            break
    return keys[:limit]


def review(client: RedisReadOnly, sample_size: int = DEFAULT_SAMPLE) -> dict[str, Any]:
    limit = max(1, min(int(sample_size), MAX_SAMPLE))
    info = parse_info(client.command("INFO"))
    maxmemory = int(_config(client, "maxmemory") or 0)
    policy = _config(client, "maxmemory-policy")
    password_set = bool(_config(client, "requirepass"))
    databases = sorted(int(k[2:]) for k in info if re.fullmatch(r"db\d+", k))
    findings: list[dict[str, str]] = []
    per_db: dict[int, dict[str, Any]] = {}
    broker_dbs: list[int] = []
    cache_dbs: list[int] = []
    big_keys: list[dict[str, Any]] = []
    for db in databases:
        client.command("SELECT", db)
        keys = _scan_sample(client, limit)
        with_ttl = 0
        prefixes: Counter[str] = Counter()
        broker = False
        expiring = 0
        for key in keys:
            ttl = client.command("TTL", key)
            if isinstance(ttl, int) and ttl >= 0:
                with_ttl += 1
                expiring += 1
            kind = client.command("TYPE", key)
            if _BROKER_KEY.match(key) or (kind == "list" and key in {"celery", "default"}):
                broker = True
            prefixes[key.split(":", 1)[0]] += 1
            usage = client.command("MEMORY", "USAGE", key)
            if isinstance(usage, int) and usage >= BIG_KEY_BYTES:
                big_keys.append({"db": db, "key": key[:120], "bytes": usage, "type": kind})
        coverage = round(with_ttl / len(keys), 2) if keys else None
        per_db[db] = {
            "sampled": len(keys),
            "ttl_coverage": coverage,
            "top_prefixes": [{"prefix": p[:60], "keys": n} for p, n in prefixes.most_common(5)],
            "broker_keys": broker,
            "keys_reported": info.get(f"db{db}", ""),
        }
        if broker:
            broker_dbs.append(db)
        if keys and expiring:
            cache_dbs.append(db)
    client.command("SELECT", 0)
    if maxmemory == 0:
        findings.append(_finding("no-maxmemory", "medium", "maxmemory is 0; memory can grow until the host runs out", "set maxmemory"))
    shared = bool(broker_dbs)
    if shared and policy.startswith("allkeys-"):
        findings.append(_finding("eviction-drops-broker", "high", f"policy {policy} with Celery broker keys on the instance; queued tasks can be evicted", "use noeviction for the broker, or move it to its own instance"))
    if shared and policy == "noeviction":
        findings.append(_finding("noeviction-shared-broker", "medium", "noeviction with a shared broker; cache writes fail with OOM once memory is full", "give the cache its own instance with an eviction policy"))
    if shared and set(broker_dbs) & set(cache_dbs):
        findings.append(_finding("broker-cache-same-db", "medium", f"broker and expiring cache keys share db {sorted(set(broker_dbs) & set(cache_dbs))}", "separate databases or instances"))
    for db, data in per_db.items():
        if data["ttl_coverage"] is not None and data["ttl_coverage"] < 0.5 and not data["broker_keys"] and policy.startswith("volatile-"):
            findings.append(_finding("low-ttl-coverage", "medium", f"db {db}: {data['ttl_coverage']:.0%} of sampled keys have a TTL and policy is {policy}", "set TTLs or use allkeys-lru"))
    if big_keys:
        findings.append(_finding("big-keys", "low", f"{len(big_keys)} sampled keys are at least 1 MiB", "split or compress the keys"))
    if not password_set:
        findings.append(_finding("no-requirepass", "medium", "requirepass is not set", "set requirepass or an ACL user"))
    return {
        "server": {"version": info.get("redis_version", ""), "used_memory": int(info.get("used_memory", 0) or 0), "maxmemory": maxmemory, "policy": policy, "password_set": password_set},
        "databases": {str(k): v for k, v in per_db.items()},
        "broker_shared": shared,
        "big_keys": sorted(big_keys, key=lambda k: k["bytes"], reverse=True)[:10],
        "findings": findings,
    }
