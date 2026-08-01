import asyncio

from app.xninetzy.interfaces.mcp_runtime import (
    configure_mcp_runtime_paths as _configure_mcp_runtime_paths,
)
from fastapi import FastAPI

from app.xninetzy.interfaces.api.routes.chat import router as chat_router
from app.xninetzy.interfaces.api.routes.debug import router as debug_router
from app.xninetzy.interfaces.api.routes.health import router as health_router
from app.xninetzy.interfaces.api.routes.reminders import router as reminders_router
from app.xninetzy.core.config import get_settings
from app.xninetzy.core.logging import configure_logging, logging
from app.xninetzy.db.sqlite import init_db
from app.xninetzy.db.migrations import run_migrations
from app.xninetzy.os.reminders.scheduler import reminder_loop
from app.xninetzy.os.jobs.service import os_job_loop
from app.xninetzy.os.academic.mahasiswa_portal.krs_watcher import krs_watcher_loop
from app.xninetzy.os.web_analysis.background import web_analysis_loop

_configure_mcp_runtime_paths()

configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="Xninetzy AI", version="2.0.0")

app.include_router(health_router)
app.include_router(chat_router, prefix="/api")
app.include_router(reminders_router, prefix="/api")

settings = get_settings()
if settings.AGENT_DEBUG_ENDPOINTS:
    app.include_router(debug_router, prefix="/api")


@app.on_event("startup")
async def startup() -> None:
    from app.xninetzy.runtime.cpu_guard import validate_cpu_only_runtime

    runtime_info = validate_cpu_only_runtime()
    logger.info("CPU-only runtime validated: %s", runtime_info)

    init_db()
    run_migrations()
    from app.xninetzy.ecosystem.reducers import replay_unconsumed_events

    replayed = replay_unconsumed_events()
    if replayed:
        logger.info("Replayed %d unconsumed ecosystem events", replayed)
    asyncio.create_task(reminder_loop())
    asyncio.create_task(os_job_loop())
    asyncio.create_task(krs_watcher_loop())
    if settings.WEB_ANALYSIS_BACKGROUND_ENABLED:
        asyncio.create_task(web_analysis_loop())
    if settings.GRAPHRAG_V3_ENABLED:
        from app.xninetzy.os.graph.v3.backfill_v1 import backfill_legacy_graph
        from app.xninetzy.os.graph.v3.graph_populator import (
            replay_unconsumed_events as replay_graph_events,
        )

        try:
            legacy = backfill_legacy_graph()
        except Exception:
            logger.exception("Graph V1 to V3 backfill failed")
        else:
            if legacy["nodes"] or legacy["edges"]:
                logger.info(
                    "Graph V1 to V3 backfilled %d nodes and %d edges",
                    legacy["nodes"],
                    legacy["edges"],
                )
        backfilled = replay_graph_events()
        if backfilled:
            logger.info("Graph populator backfilled %d events", backfilled)
        from app.xninetzy.os.graph.v3.projection_worker import projection_worker_loop

        asyncio.create_task(projection_worker_loop())
        if settings.GRAPH_COMMUNITY_ENABLED:
            from app.xninetzy.os.graph.v3.community_builder import community_loop

            asyncio.create_task(community_loop())
    if settings.HEBAT_AUTO_LOGIN:
        from app.xninetzy.os.academic.mahasiswa_portal.credential_provider import (
            CampusCredentialError,
            resolve_campus_credentials,
        )

        try:
            resolve_campus_credentials("hebat")
        except CampusCredentialError as exc:
            logger.warning("HEBAT auto-login skipped: %s", exc)
        else:
            asyncio.create_task(_hebat_startup_task())


def _hebat_session_chat_id(s) -> str | None:
    """Resolve the chat id used to key the HEBAT browser session/profile."""
    raw = (s.HEBAT_NOTIFY_CHAT_ID or s.ADMIN_JID or "").strip()
    if not raw:
        return None
    if not raw.endswith(("@s.whatsapp.net", "@g.us")):
        raw = raw + "@s.whatsapp.net"
    return raw


async def _hebat_startup_task() -> None:
    """Auto-login to HEBAT on startup (credentials from env), verify, then notify admin."""
    await asyncio.sleep(5)  # let the service finish booting
    s = get_settings()
    from app.xninetzy.os.academic.mahasiswa_portal.credential_provider import (
        CampusCredentialError,
        resolve_campus_credentials,
    )

    try:
        credentials = resolve_campus_credentials("hebat")
    except CampusCredentialError as exc:
        logger.warning("HEBAT auto-login skipped: %s", exc)
        return
    chat_id = _hebat_session_chat_id(s)
    if not chat_id:
        logger.warning(
            "HEBAT auto-login skipped: set HEBAT_NOTIFY_CHAT_ID or ADMIN_JID to key the session"
        )
        return
    notify_id = chat_id if s.HEBAT_NOTIFY_CHAT_ID else None

    try:
        from app.xninetzy.os.academic.hebat.browser_session import ensure_hebat_session

        logger.info("HEBAT auto-login starting (chat_id=%s)", chat_id)
        ok, profile, courses = await ensure_hebat_session(
            chat_id,
            credentials.username,
            credentials.password.get_secret_value(),
        )
        if not ok:
            logger.error("HEBAT auto-login failed after retries")
            if notify_id:
                await _notify_wa(
                    notify_id,
                    "⚠️ Xninetzy AI: Auto-login HEBAT gagal setelah beberapa percobaan. "
                    "Cek kredensial atau koneksi ke HEBAT.",
                )
            return

        logger.info("HEBAT auto-login OK (profile=%s, courses=%d)", profile, courses)
        if notify_id:
            from app.xninetzy.os.academic.hebat.tools import hebat_academic_digest

            digest = hebat_academic_digest.invoke({"chat_id": chat_id, "days_ahead": 7})
            await _notify_wa(
                notify_id,
                f"🤖 *Xninetzy AI Online*\n\n"
                f"Sesi HEBAT aktif sebagai *{profile or credentials.username}* ({courses} course)\n\n"
                f"{digest}",
            )

    except Exception as e:
        logger.error("HEBAT startup task failed: %s", e)
        if notify_id:
            try:
                await _notify_wa(notify_id, f"⚠️ Xninetzy AI: Startup HEBAT error — {e}")
            except Exception:
                pass


async def _notify_wa(chat_id: str, text: str) -> None:
    """Send a WA message via MCP — best-effort, no crash if MCP not ready."""
    try:
        from app.xninetzy.interfaces.whatsapp.client import call_wa_tool

        await call_wa_tool("send_text_message", {"jid": chat_id, "text": text})
    except Exception as e:
        logger.warning("Startup WA notification failed: %s", e)
