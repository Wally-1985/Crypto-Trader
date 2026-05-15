from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.wallets import IntelligencePipelineRunSummary
from app.services.pipeline import run_intelligence_pipeline_once

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.post("/run-once", response_model=IntelligencePipelineRunSummary)
def run_pipeline_once(
    polling_provider: str = Query(default="etherscan_readonly", pattern="^(dry_run|mock|etherscan_readonly)$"),
    enrichment_provider: str = Query(default="coingecko_public", pattern="^coingecko_public$"),
    outcome_provider: str = Query(default="coingecko_public", pattern="^(mock|coingecko_public)$"),
    db: Session = Depends(get_db),
) -> IntelligencePipelineRunSummary:
    summary = run_intelligence_pipeline_once(
        db,
        polling_provider=polling_provider,
        enrichment_provider=enrichment_provider,
        outcome_provider=outcome_provider,
    )
    return IntelligencePipelineRunSummary(**summary.__dict__)
