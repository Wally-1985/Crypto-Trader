from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.wallets import AgentAlert, AgentAlertUpdate

router = APIRouter(prefix="/agent-alerts", tags=["agent-alerts"])


def _row_to_dict(row: Any) -> dict[str, Any]:
    return dict(row._mapping)


@router.get("", response_model=list[AgentAlert])
def list_alerts(
    manual_review_required: bool | None = Query(default=None),
    acknowledged: bool | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    severity: str | None = Query(default=None),
    candidate_decision: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    filters: list[str] = []
    params: dict[str, Any] = {"limit": limit}
    if manual_review_required is not None:
        filters.append("manual_review_required = :manual_review_required")
        params["manual_review_required"] = manual_review_required
    if acknowledged is not None:
        filters.append("acknowledged_at IS NOT NULL" if acknowledged else "acknowledged_at IS NULL")
    if status_filter is not None:
        filters.append("status = :status_filter")
        params["status_filter"] = status_filter
    if severity is not None:
        filters.append("severity = :severity")
        params["severity"] = severity
    if candidate_decision is not None:
        filters.append("candidate_decision = :candidate_decision")
        params["candidate_decision"] = candidate_decision
    where_clause = "WHERE " + " AND ".join(filters) if filters else ""
    rows = db.execute(
        text(
            f"""
            SELECT *
            FROM agent_alerts
            {where_clause}
            ORDER BY created_at DESC
            LIMIT :limit
            """
        ),
        params,
    ).fetchall()
    return [_row_to_dict(row) for row in rows]


@router.patch("/{alert_id}", response_model=AgentAlert)
def update_alert(alert_id: UUID, payload: AgentAlertUpdate, db: Session = Depends(get_db)) -> dict[str, Any]:
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        row = db.execute(text("SELECT * FROM agent_alerts WHERE id = :alert_id"), {"alert_id": alert_id}).fetchone()
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="alert not found")
        return _row_to_dict(row)
    allowed = {"status", "analyst_notes", "candidate_decision"}
    set_clauses = [f"{field} = :{field}" for field in updates if field in allowed]
    if updates.get("status") == "acknowledged":
        set_clauses.append("acknowledged_at = COALESCE(acknowledged_at, now())")
    params = {**updates, "alert_id": alert_id}
    row = db.execute(
        text(
            f"""
            UPDATE agent_alerts
            SET {', '.join(set_clauses)}
            WHERE id = :alert_id
            RETURNING *
            """
        ),
        params,
    ).fetchone()
    if row is None:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="alert not found")
    db.commit()
    return _row_to_dict(row)


@router.patch("/{alert_id}/acknowledge", response_model=AgentAlert)
def acknowledge_alert(alert_id: UUID, db: Session = Depends(get_db)) -> dict[str, Any]:
    row = db.execute(
        text(
            """
            UPDATE agent_alerts
            SET acknowledged_at = COALESCE(acknowledged_at, now()), status = 'acknowledged'
            WHERE id = :alert_id
            RETURNING *
            """
        ),
        {"alert_id": alert_id},
    ).fetchone()
    if row is None:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="alert not found")
    db.commit()
    return _row_to_dict(row)
