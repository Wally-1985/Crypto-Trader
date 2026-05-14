from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.wallets import PollingRunSummary
from app.workers.wallet_polling import run_wallet_polling_once

router = APIRouter(prefix="/wallet-polling", tags=["wallet-polling"])


@router.post("/run-once", response_model=PollingRunSummary)
def run_polling_once(db: Session = Depends(get_db)) -> dict:
    """Run the Stage 1 dry-run wallet polling skeleton once."""
    return run_wallet_polling_once(db)
