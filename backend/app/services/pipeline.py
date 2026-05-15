from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.services.movement_enrichment import run_movement_enrichment
from app.services.run_logs import finish_run_log, start_run_log
from app.services.signal_outcomes import run_due_outcome_backfill
from app.workers.wallet_polling import provider_for_name, run_wallet_polling_once


@dataclass(frozen=True)
class IntelligencePipelineSummary:
    provider: str
    polling: dict[str, Any]
    enrichment: dict[str, Any]
    outcomes: dict[str, Any]
    checked_wallets: int
    fetched_movements: int
    created_movements: int
    enriched_movements: int
    created_outcomes: int
    provider_errors: int
    status: str
    paper_trading_only: bool = True


def run_intelligence_pipeline_once(
    db: Session,
    *,
    polling_provider: str = "etherscan_readonly",
    enrichment_provider: str = "coingecko_public",
    outcome_provider: str = "coingecko_public",
    enrichment_limit: int = 500,
    outcome_limit: int = 500,
) -> IntelligencePipelineSummary:
    """Run the wallet-led intelligence pipeline once, without trading or signing.

    Order is intentionally fixed: ingest watched-wallet transfers, enrich movements,
    then score due outcomes. Provider failures are summarized and logged for review.
    """
    run_id, started = start_run_log(
        db,
        run_type="pipeline",
        provider="wallet_intelligence",
        metadata={
            "polling_provider": polling_provider,
            "enrichment_provider": enrichment_provider,
            "outcome_provider": outcome_provider,
            "paper_trading_only": True,
        },
    )
    try:
        polling = run_wallet_polling_once(db, provider_for_name(polling_provider))
        enrichment_result = run_movement_enrichment(db, provider_name=enrichment_provider, limit=enrichment_limit, commit=True)
        outcomes_result = run_due_outcome_backfill(db, provider_name=outcome_provider, limit=outcome_limit, commit=True)

        enrichment = enrichment_result.__dict__
        outcomes = outcomes_result.__dict__
        provider_errors = int(polling.get("provider_errors") or 0) + int(enrichment.get("provider_errors") or 0) + int(outcomes.get("provider_errors") or 0)
        skipped_reason = polling.get("skipped_reason")
        status = "skipped" if skipped_reason else "partial" if provider_errors else "success"
        summary = IntelligencePipelineSummary(
            provider="wallet_intelligence",
            polling=polling,
            enrichment=enrichment,
            outcomes=outcomes,
            checked_wallets=int(polling.get("checked_wallets") or 0),
            fetched_movements=int(polling.get("fetched_movements") or 0),
            created_movements=int(polling.get("created_movements") or 0),
            enriched_movements=int(enrichment.get("enriched_movements") or 0),
            created_outcomes=int(outcomes.get("created_outcomes") or 0),
            provider_errors=provider_errors,
            status=status,
        )
        finish_run_log(
            db,
            run_id=run_id,
            started_perf=started,
            status=status,
            summary={
                "checked_wallets": summary.checked_wallets,
                "fetched_movements": summary.fetched_movements,
                "created_movements": summary.created_movements,
                "enriched_movements": summary.enriched_movements,
                "created_outcomes": summary.created_outcomes,
                "provider_errors": summary.provider_errors,
                "skipped_reason": skipped_reason,
            },
            metadata={"polling": polling, "enrichment": enrichment, "outcomes": outcomes, "paper_trading_only": True},
        )
        return summary
    except Exception as exc:
        finish_run_log(
            db,
            run_id=run_id,
            started_perf=started,
            status="failed",
            summary={"provider_errors": 1, "skipped_reason": str(exc)},
            metadata={"error": str(exc), "paper_trading_only": True},
        )
        raise
