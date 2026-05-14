from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.wallets import PollingRunSummary
from app.workers.wallet_polling import provider_for_name, run_wallet_polling_once

router = APIRouter(prefix="/wallet-polling", tags=["wallet-polling"])


@router.post("/run-once", response_model=PollingRunSummary)
def run_polling_once(
    provider: str = Query(default="dry_run", pattern="^(dry_run|mock|etherscan_readonly)$"),
    db: Session = Depends(get_db),
) -> dict:
    """Run the Stage 1 wallet polling pipeline once.

    `dry_run` performs no external work. `mock` creates deterministic fake movements.
    `etherscan_readonly` pulls watched-wallet Ethereum transfers only when an
    ETHERSCAN_API_KEY is configured; it never signs or trades.
    """
    return run_wallet_polling_once(db, provider_for_name(provider))
