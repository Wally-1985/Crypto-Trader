from fastapi import APIRouter

from app.core.config import settings
from app.core.model_routing import routing_summary

router = APIRouter()


@router.get("/health")
def health() -> dict[str, object]:
    return {
        "status": "ok",
        "app_version": settings.app_version,
        "live_trading_enabled": settings.live_trading_enabled,
        "paper_trading_enabled": settings.paper_trading_enabled,
        "model_routing": routing_summary(),
    }
