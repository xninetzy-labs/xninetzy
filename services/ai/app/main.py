import asyncio

from fastapi import FastAPI

from app.api.routes.chat import router as chat_router
from app.api.routes.debug import router as debug_router
from app.api.routes.health import router as health_router
from app.api.routes.reminders import router as reminders_router
from app.core.config import get_settings
from app.core.logging import configure_logging, logging
from app.db.sqlite import init_db
from app.db.migrations import run_migrations
from app.reminders.scheduler import reminder_loop

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
    init_db()
    run_migrations()
    asyncio.create_task(reminder_loop())
    if settings.HEBAT_AUTO_LOGIN and settings.HEBAT_USERNAME and settings.HEBAT_PASSWORD:
        asyncio.create_task(_hebat_startup_task())
    elif settings.HEBAT_AUTO_LOGIN:
        logger.warning("HEBAT auto-login enabled but HEBAT_USERNAME/HEBAT_PASSWORD missing in env")


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
    chat_id = _hebat_session_chat_id(s)
    if not chat_id:
        logger.warning(
            "HEBAT auto-login skipped: set HEBAT_NOTIFY_CHAT_ID or ADMIN_JID to key the session"
        )
        return
    notify_id = chat_id if s.HEBAT_NOTIFY_CHAT_ID else None

    try:
        from app.tools.hebat.browser_session import ensure_hebat_session

        logger.info("HEBAT auto-login starting (chat_id=%s)", chat_id)
        ok, profile, courses = await ensure_hebat_session(
            chat_id, s.HEBAT_USERNAME, s.HEBAT_PASSWORD
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
            from app.tools.hebat.tools import hebat_academic_digest

            digest = hebat_academic_digest.invoke({"chat_id": chat_id, "days_ahead": 7})
            await _notify_wa(
                notify_id,
                f"🤖 *Xninetzy AI Online*\n\n"
                f"Sesi HEBAT aktif sebagai *{profile or s.HEBAT_USERNAME}* ({courses} course)\n\n"
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
        from app.wa_tools.client import call_wa_tool
        await call_wa_tool("send_text_message", {"jid": chat_id, "text": text})
    except Exception as e:
        logger.warning("Startup WA notification failed: %s", e)
