from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.wallets import MovementEnrichmentRunSummary
from app.services.movement_enrichment import run_movement_enrichment
from app.services.run_logs import run_with_log

router = APIRouter(prefix="/movement-enrichment", tags=["movement-enrichment"])


@router.post("/run-once", response_model=MovementEnrichmentRunSummary)
def run_enrichment_once(
    provider: str = Query(default="coingecko_public", pattern="^coingecko_public$"),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> MovementEnrichmentRunSummary:
    summary = run_with_log(
        db,
        run_type="movement_enrichment",
        provider=provider,
        operation=lambda: run_movement_enrichment(db, provider_name=provider, limit=limit, commit=True),
        summary_to_dict=lambda result: result.__dict__,
    )
    return MovementEnrichmentRunSummary(**summary.__dict__)
