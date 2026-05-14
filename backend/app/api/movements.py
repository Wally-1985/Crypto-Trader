from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.wallets import WalletMovement, WalletMovementCreate
from app.services.movement_ingestion import ingest_wallet_movement

router = APIRouter(prefix="/wallet-movements", tags=["wallet-movements"])


def _row_to_dict(row: Any) -> dict[str, Any]:
    return dict(row._mapping)


@router.get("", response_model=list[WalletMovement])
def list_movements(
    wallet_id: UUID | None = Query(default=None),
    chain: str | None = Query(default=None),
    token_symbol: str | None = Query(default=None),
    manual_review_required: bool | None = Query(default=None),
    alert_threshold_crossed: bool | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    filters: list[str] = []
    params: dict[str, Any] = {"limit": limit}
    if wallet_id is not None:
        filters.append("wallet_id = :wallet_id")
        params["wallet_id"] = wallet_id
    if chain is not None:
        filters.append("chain = :chain")
        params["chain"] = chain
    if token_symbol is not None:
        filters.append("token_symbol = :token_symbol")
        params["token_symbol"] = token_symbol.upper()
    if manual_review_required is not None:
        filters.append("manual_review_required = :manual_review_required")
        params["manual_review_required"] = manual_review_required
    if alert_threshold_crossed is not None:
        filters.append("alert_threshold_crossed = :alert_threshold_crossed")
        params["alert_threshold_crossed"] = alert_threshold_crossed

    where_clause = "WHERE " + " AND ".join(filters) if filters else ""
    rows = db.execute(
        text(
            f"""
            SELECT *
            FROM wallet_movements
            {where_clause}
            ORDER BY transaction_time DESC, created_at DESC
            LIMIT :limit
            """
        ),
        params,
    ).fetchall()
    return [_row_to_dict(row) for row in rows]


@router.post("", response_model=WalletMovement, status_code=status.HTTP_201_CREATED)
def create_movement(payload: WalletMovementCreate, db: Session = Depends(get_db)) -> dict[str, Any]:
    try:
        movement, created = ingest_wallet_movement(db, payload.model_dump(), commit=True)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    if not created or movement is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="movement already exists for this wallet/transaction or violates movement policy",
        )
    return movement
