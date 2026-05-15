from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.wallets import PipelineRunLog
from app.services.run_logs import list_run_logs

router = APIRouter(prefix="/pipeline-runs", tags=["pipeline-runs"])


@router.get("", response_model=list[PipelineRunLog])
def get_pipeline_runs(
    run_type: str | None = Query(default=None, pattern="^(wallet_polling|movement_enrichment|signal_outcomes|pipeline)$"),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[dict]:
    return list_run_logs(db, limit=limit, run_type=run_type)
