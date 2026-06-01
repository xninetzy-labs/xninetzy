import asyncio

from fastapi import FastAPI

from app.api.routes.chat import router as chat_router
from app.api.routes.health import router as health_router
from app.api.routes.obsidian import router as obsidian_router
from app.api.routes.reminders import router as reminders_router
from app.api.routes.skills import router as skills_router
from app.core.logging import configure_logging
from app.db.sqlite import init_db
from app.reminders.scheduler import reminder_loop

configure_logging()

app = FastAPI(title="Xninetzy AI", version="0.1.0")

app.include_router(health_router)
app.include_router(chat_router, prefix="/api")
app.include_router(skills_router, prefix="/api")
app.include_router(obsidian_router, prefix="/api")
app.include_router(reminders_router, prefix="/api")


@app.on_event("startup")
async def startup() -> None:
    init_db()
    asyncio.create_task(reminder_loop())
