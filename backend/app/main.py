from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.wallets import router as wallets_router
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Crypto wallet intelligence backend. V1 is research and paper-trading only; live trading is disabled.",
)

app.include_router(health_router, tags=["health"])
app.include_router(wallets_router)
