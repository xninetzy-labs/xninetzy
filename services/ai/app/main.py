import asyncio

from fastapi import FastAPI

from app.api.routes.chat import router as chat_router
from app.api.routes.debug import router as debug_router
from app.api.routes.health import router as health_router
from app.api.routes.reminders import router as reminders_router
from app.core.config import get_settings
from app.core.logging import configure_logging, logging
from app.db.sqlite import init_db
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
    asyncio.create_task(reminder_loop())
    if settings.HEBAT_USERNAME and settings.HEBAT_NOTIFY_CHAT_ID:
        asyncio.create_task(_hebat_startup_task())


async def _hebat_startup_task() -> None:
    """Auto-login to HEBAT and send digest to admin on startup."""
    await asyncio.sleep(5)  # Wait for service to be fully ready
    s = get_settings()
    chat_id = s.HEBAT_NOTIFY_CHAT_ID
    if not chat_id.endswith(("@s.whatsapp.net", "@g.us")):
        chat_id = chat_id + "@s.whatsapp.net"

    try:
        from app.tools.hebat.browser_session import check_session_valid, login_with_credentials
        from app.tools.hebat.storage import get_session

        logger.info("HEBAT startup: checking session for %s", chat_id)
        is_valid, profile_name = await check_session_valid(chat_id)

        if not is_valid:
            logger.info("HEBAT startup: session invalid, auto-login...")
            success = await login_with_credentials(chat_id, s.HEBAT_USERNAME, s.HEBAT_PASSWORD)
            if not success:
                await _notify_wa(chat_id, "⚠️ Xninetzy AI: Auto-login HEBAT gagal. Cek kredensial di .env")
                return
            session = get_session(chat_id)
            profile_name = session.get("profile_name") if session else s.HEBAT_USERNAME
            logger.info("HEBAT startup: login success, profile=%s", profile_name)

        # Send startup digest
        from app.tools.hebat.tools import hebat_academic_digest
        digest = hebat_academic_digest.invoke({"chat_id": chat_id, "days_ahead": 7})
        startup_msg = f"🤖 *Xninetzy AI Online*\n\nSesi HEBAT aktif sebagai *{profile_name}*\n\n{digest}"
        await _notify_wa(chat_id, startup_msg)

    except Exception as e:
        logger.error("HEBAT startup task failed: %s", e)
        try:
            await _notify_wa(chat_id, f"⚠️ Xninetzy AI: Startup HEBAT error — {e}")
        except Exception:
            pass


async def _notify_wa(chat_id: str, text: str) -> None:
    """Send a WA message via MCP — best-effort, no crash if MCP not ready."""
    try:
        from app.wa_tools.client import call_wa_tool
        await call_wa_tool("send_text_message", {"jid": chat_id, "text": text})
    except Exception as e:
        logger.warning("Startup WA notification failed: %s", e)
