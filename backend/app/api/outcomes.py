from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.wallets import SignalOutcome, SignalOutcomeRunSummary, SignalOutcomeSummary
from app.services.run_logs import run_with_log
from app.services.signal_outcomes import list_signal_outcomes, run_due_outcome_backfill, run_mock_outcome_backfill, summarize_signal_outcomes

router = APIRouter(prefix="/signal-outcomes", tags=["signal-outcomes"])


@router.get("", response_model=list[SignalOutcome])
def list_outcomes(
    wallet_id: UUID | None = Query(default=None),
    token_symbol: str | None = Query(default=None),
    horizon: str | None = Query(default=None),
    signal_result: str | None = Query(default=None),
    provider: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    return list_signal_outcomes(
        db,
        wallet_id=wallet_id,
        token_symbol=token_symbol,
        horizon=horizon,
        signal_result=signal_result,
        provider=provider,
        limit=limit,
    )


@router.get("/summary", response_model=SignalOutcomeSummary)
def outcome_summary(db: Session = Depends(get_db)) -> dict[str, Any]:
    return summarize_signal_outcomes(db)


@router.post("/run-once", response_model=SignalOutcomeRunSummary)
def run_outcome_backfill(
    provider: str = Query(default="mock", pattern="^mock$"),
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
) -> SignalOutcomeRunSummary:
    summary = run_with_log(
        db,
        run_type="signal_outcomes",
        provider=provider,
        operation=lambda: run_mock_outcome_backfill(db, limit=limit, commit=True),
        summary_to_dict=lambda result: result.__dict__,
    )
    return SignalOutcomeRunSummary(**summary.__dict__)


@router.post("/run-due", response_model=SignalOutcomeRunSummary)
def run_due_outcomes(
    provider: str = Query(default="mock", pattern="^(mock|coingecko_public)$"),
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
) -> SignalOutcomeRunSummary:
    summary = run_with_log(
        db,
        run_type="signal_outcomes",
        provider=provider,
        operation=lambda: run_due_outcome_backfill(db, provider_name=provider, limit=limit, commit=True),
        summary_to_dict=lambda result: result.__dict__,
    )
    return SignalOutcomeRunSummary(**summary.__dict__)
