from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.wallets import WalletPerformance
from app.services.wallet_performance import list_wallet_performance

router = APIRouter(prefix="/wallet-performance", tags=["wallet-performance"])


@router.get("", response_model=list[WalletPerformance])
def wallet_performance(
    provider: str | None = Query(default=None),
    horizon: str | None = Query(default=None),
    min_outcomes: int = Query(default=0, ge=0, le=1000),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    return list_wallet_performance(
        db,
        provider=provider,
        horizon=horizon,
        min_outcomes=min_outcomes,
        limit=limit,
    )
