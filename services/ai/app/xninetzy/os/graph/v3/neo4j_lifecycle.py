"""On-demand Neo4j lifecycle for host-mode MCP.

The MCP stdio server runs on the host, outside the compose network, so the
``graph`` profile's neo4j container is not started by a plain ``docker compose
up`` and its docker-DNS hostname is unreachable. This module boots the
container on first graph access (``docker compose --profile graph up -d
neo4j``), polls bolt-readiness, and stops it again once graph tools have been
idle — so Neo4j only runs while it is actually in use.

Everything here is best-effort: Neo4j is a rebuildable projection, never the
source of truth. Every failure is swallowed and logged; if Docker is absent or
the boot times out, the caller simply degrades to the SQLite/FAISS legs.
"""

from __future__ import annotations

import atexit
import socket
import subprocess
import threading
import time
from pathlib import Path

from app.xninetzy.core.config import get_settings
from app.xninetzy.core.logging import logging
from app.xninetzy.interfaces import mcp_runtime

logger = logging.getLogger(__name__)

_last_access = 0.0
_last_access_lock = threading.Lock()
_idle_thread_lock = threading.Lock()
_idle_thread_started = False
_boot_lock = threading.Lock()
_atexit_registered = False
_started_here = False  # we booted the container (so we own stopping it on exit)


def is_host_runtime() -> bool:
    """Reuse the MCP path-resolver's host-mode rule (no docker-DNS on host)."""
    try:
        return mcp_runtime.is_host_runtime()
    except Exception:
        return False


def _compose_root() -> Path:
    """Repository root holding docker-compose.yml (parent of ``services/ai``)."""
    return mcp_runtime.ai_service_root().parents[1]


def _bolt_endpoint(settings) -> tuple[str, int]:
    uri = settings.NEO4J_HOST_URI or "bolt://127.0.0.1:7687"
    rest = uri.split("://", 1)[-1]
    host, _, port = rest.partition(":")
    return host or "127.0.0.1", int(port or 7687)


def _bolt_ready(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def touch_access() -> None:
    global _last_access
    with _last_access_lock:
        _last_access = time.monotonic()


def _compose_cmd(settings, *args: str) -> list[str]:
    return [
        "docker", "compose",
        "--profile", settings.NEO4J_AUTOSTART_PROFILE,
        *args,
    ]


def ensure_running() -> bool:
    """Boot the neo4j container on demand and wait for bolt. Best-effort.

    Returns True when bolt is reachable (already up, or booted here). Records an
    access and starts the idle-watch loop so the container is stopped again once
    graph tools go quiet.
    """
    settings = get_settings()
    if not (settings.NEO4J_AUTOSTART_ENABLED and is_host_runtime()):
        return False

    global _started_here
    host, port = _bolt_endpoint(settings)
    service = settings.NEO4J_AUTOSTART_COMPOSE_SERVICE

    if _bolt_ready(host, port):
        touch_access()
        _start_idle_watch()
        return True

    with _boot_lock:
        # Another thread may have booted it while we waited on the lock.
        if _bolt_ready(host, port):
            touch_access()
            _start_idle_watch()
            return True
        try:
            subprocess.run(
                _compose_cmd(settings, "up", "-d", service),
                cwd=_compose_root(),
                capture_output=True,
                timeout=settings.NEO4J_AUTOSTART_BOOT_TIMEOUT_SECONDS,
                check=False,
            )
        except Exception as e:
            logger.warning("Neo4j autostart 'up' failed (non-fatal): %s", e)
            return False

        deadline = time.monotonic() + settings.NEO4J_AUTOSTART_BOOT_TIMEOUT_SECONDS
        while time.monotonic() < deadline:
            if _bolt_ready(host, port):
                _started_here = True
                touch_access()
                _start_idle_watch()
                _register_atexit()
                return True
            time.sleep(1.0)
        logger.warning("Neo4j autostart timed out waiting for bolt at %s:%s", host, port)
        return False


def stop() -> None:
    """Stop the neo4j container. Best-effort; resets neo4j_store so a later
    access re-boots and reconnects cleanly."""
    settings = get_settings()
    service = settings.NEO4J_AUTOSTART_COMPOSE_SERVICE
    try:
        subprocess.run(
            _compose_cmd(settings, "stop", service),
            cwd=_compose_root(),
            capture_output=True,
            timeout=30,
            check=False,
        )
    except Exception as e:
        logger.warning("Neo4j autostart 'stop' failed (non-fatal): %s", e)
    _reset_store()


def _reset_store() -> None:
    """Drop the cached driver and clear the sticky-unavailable flag so the next
    access can boot and reconnect."""
    try:
        from app.xninetzy.os.graph.v3 import neo4j_store

        neo4j_store.close_driver()
        neo4j_store.clear_unavailable()
    except Exception:
        pass


def _idle_watch_loop() -> None:
    settings = get_settings()
    host, port = _bolt_endpoint(settings)
    idle_stop = settings.NEO4J_AUTOSTART_IDLE_STOP_SECONDS
    if idle_stop <= 0:
        return  # idle-stop disabled; container stays up until process exit
    poll = max(5, min(30, idle_stop))
    while True:
        time.sleep(poll)
        try:
            with _last_access_lock:
                idle = time.monotonic() - _last_access
            if idle < idle_stop:
                continue
            if not _bolt_ready(host, port):
                continue
            logger.info("Neo4j idle %.0fs > %ss — stopping container", idle, idle_stop)
            stop()
        except Exception as e:
            logger.warning("Neo4j idle-watch iteration failed (non-fatal): %s", e)


def _register_atexit() -> None:
    global _atexit_registered
    with _idle_thread_lock:
        if _atexit_registered:
            return
        _atexit_registered = True
    atexit.register(_atexit_stop)


def _atexit_stop() -> None:
    """Stop the container on process exit only if we started it and the policy
    asks for it. An externally-running Neo4j is left untouched."""
    if not _started_here:
        return
    if not get_settings().NEO4J_AUTOSTART_STOP_ON_EXIT:
        return
    stop()


def _start_idle_watch() -> None:
    global _idle_thread_started
    with _idle_thread_lock:
        if _idle_thread_started:
            return
        _idle_thread_started = True
    t = threading.Thread(target=_idle_watch_loop, name="neo4j-idle-watch", daemon=True)
    t.start()
