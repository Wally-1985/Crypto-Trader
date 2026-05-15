import json
from datetime import datetime, timezone
from time import perf_counter
from typing import Any, Callable, TypeVar

from sqlalchemy import text
from sqlalchemy.orm import Session

T = TypeVar("T")


def start_run_log(db: Session, *, run_type: str, provider: str, metadata: dict[str, Any] | None = None) -> tuple[str, float]:
    row = db.execute(
        text(
            """
            INSERT INTO pipeline_run_logs (run_type, provider, status, metadata)
            VALUES (:run_type, :provider, 'started', CAST(:metadata AS jsonb))
            RETURNING id
            """
        ),
        {"run_type": run_type, "provider": provider, "metadata": json.dumps(metadata or {}, default=str)},
    ).fetchone()
    db.commit()
    return str(row._mapping["id"]), perf_counter()


def finish_run_log(
    db: Session,
    *,
    run_id: str,
    started_perf: float,
    status: str,
    summary: dict[str, Any],
    metadata: dict[str, Any] | None = None,
) -> None:
    duration_ms = int((perf_counter() - started_perf) * 1000)
    db.execute(
        text(
            """
            UPDATE pipeline_run_logs
            SET status = :status,
                finished_at = :finished_at,
                duration_ms = :duration_ms,
                checked_wallets = :checked_wallets,
                checked_movements = :checked_movements,
                fetched_movements = :fetched_movements,
                created_movements = :created_movements,
                enriched_movements = :enriched_movements,
                created_outcomes = :created_outcomes,
                skipped_duplicates = :skipped_duplicates,
                skipped_existing = :skipped_existing,
                provider_errors = :provider_errors,
                skipped_reason = :skipped_reason,
                metadata = metadata || CAST(:metadata AS jsonb)
            WHERE id = :run_id
            """
        ),
        {
            "run_id": run_id,
            "status": status,
            "finished_at": datetime.now(timezone.utc),
            "duration_ms": duration_ms,
            "checked_wallets": summary.get("checked_wallets") or 0,
            "checked_movements": summary.get("checked_movements") or summary.get("checked_due_outcomes") or 0,
            "fetched_movements": summary.get("fetched_movements") or 0,
            "created_movements": summary.get("created_movements") or 0,
            "enriched_movements": summary.get("enriched_movements") or 0,
            "created_outcomes": summary.get("created_outcomes") or 0,
            "skipped_duplicates": summary.get("skipped_duplicates") or 0,
            "skipped_existing": summary.get("skipped_existing") or 0,
            "provider_errors": summary.get("provider_errors") or 0,
            "skipped_reason": summary.get("skipped_reason"),
            "metadata": json.dumps(metadata or summary, default=str),
        },
    )
    db.commit()


def run_with_log(
    db: Session,
    *,
    run_type: str,
    provider: str,
    operation: Callable[[], T],
    summary_to_dict: Callable[[T], dict[str, Any]] = lambda result: dict(result),
) -> T:
    run_id, started = start_run_log(db, run_type=run_type, provider=provider)
    try:
        result = operation()
        summary = summary_to_dict(result)
        status = "skipped" if summary.get("skipped_reason") else "partial" if summary.get("provider_errors") else "success"
        finish_run_log(db, run_id=run_id, started_perf=started, status=status, summary=summary)
        return result
    except Exception as exc:
        finish_run_log(
            db,
            run_id=run_id,
            started_perf=started,
            status="failed",
            summary={"provider_errors": 1, "skipped_reason": str(exc)},
            metadata={"error": str(exc)},
        )
        raise


def list_run_logs(db: Session, *, limit: int = 50, run_type: str | None = None) -> list[dict[str, Any]]:
    filters = []
    params: dict[str, Any] = {"limit": limit}
    if run_type:
        filters.append("run_type = :run_type")
        params["run_type"] = run_type
    where_clause = "WHERE " + " AND ".join(filters) if filters else ""
    rows = db.execute(
        text(
            f"""
            SELECT *
            FROM pipeline_run_logs
            {where_clause}
            ORDER BY started_at DESC
            LIMIT :limit
            """
        ),
        params,
    ).fetchall()
    return [dict(row._mapping) for row in rows]
