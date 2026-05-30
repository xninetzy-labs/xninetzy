from fastapi import FastAPI

from app.api.routes.chat import router as chat_router
from app.api.routes.health import router as health_router
from app.core.logging import configure_logging

configure_logging()

app = FastAPI(title="Xninetzy AI", version="0.1.0")

app.include_router(health_router)
app.include_router(chat_router, prefix="/api")
