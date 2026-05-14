from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.alerts import router as alerts_router
from app.api.health import router as health_router
from app.api.movements import router as movements_router
from app.api.outcomes import router as outcomes_router
from app.api.performance import router as performance_router
from app.api.polling import router as polling_router
from app.api.tokens import router as tokens_router
from app.api.wallets import router as wallets_router
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Crypto wallet intelligence backend. V1 is research and paper-trading only; live trading is disabled.",
)

allowed_origins = [origin.strip() for origin in settings.cors_allowed_origins.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type"],
)

app.include_router(health_router, tags=["health"])
app.include_router(wallets_router)
app.include_router(movements_router)
app.include_router(alerts_router)
app.include_router(polling_router)
app.include_router(outcomes_router)
app.include_router(performance_router)
app.include_router(tokens_router)
