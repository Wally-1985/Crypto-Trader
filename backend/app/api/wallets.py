from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.wallets import WhaleWallet, WhaleWalletCreate, WalletSummary

router = APIRouter(prefix="/wallets", tags=["wallets"])


def _row_to_dict(row: Any) -> dict[str, Any]:
    return dict(row._mapping)


@router.get("", response_model=list[WhaleWallet])
def list_wallets(
    enabled: bool | None = Query(default=None),
    chain: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    filters: list[str] = []
    params: dict[str, Any] = {"limit": limit}
    if enabled is not None:
        filters.append("enabled = :enabled")
        params["enabled"] = enabled
    if chain is not None:
        filters.append("chain = :chain")
        params["chain"] = chain
    where_clause = "WHERE " + " AND ".join(filters) if filters else ""
    rows = db.execute(
        text(
            f"""
            SELECT *
            FROM whale_wallets
            {where_clause}
            ORDER BY watch_priority ASC, updated_at DESC
            LIMIT :limit
            """
        ),
        params,
    ).fetchall()
    return [_row_to_dict(row) for row in rows]


@router.post("", response_model=WhaleWallet, status_code=status.HTTP_201_CREATED)
def create_wallet(payload: WhaleWalletCreate, db: Session = Depends(get_db)) -> dict[str, Any]:
    values = payload.model_dump()
    values["normalized_address"] = payload.normalized_address
    try:
        row = db.execute(
            text(
                """
                INSERT INTO whale_wallets (
                    wallet_address,
                    normalized_address,
                    chain,
                    label,
                    wallet_type,
                    notes,
                    enabled,
                    alert_threshold_usd,
                    watch_priority,
                    confidence_weighting,
                    copy_trade_enabled,
                    do_not_copy,
                    tags,
                    sectors_of_interest
                ) VALUES (
                    :wallet_address,
                    :normalized_address,
                    :chain,
                    :label,
                    :wallet_type,
                    :notes,
                    :enabled,
                    :alert_threshold_usd,
                    :watch_priority,
                    :confidence_weighting,
                    :copy_trade_enabled,
                    :do_not_copy,
                    :tags,
                    :sectors_of_interest
                )
                RETURNING *
                """
            ),
            values,
        ).fetchone()
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="wallet already exists for this chain or violates wallet policy",
        ) from exc
    return _row_to_dict(row)


@router.patch("/{wallet_id}/enabled", response_model=WhaleWallet)
def set_wallet_enabled(wallet_id: UUID, enabled: bool, db: Session = Depends(get_db)) -> dict[str, Any]:
    row = db.execute(
        text(
            """
            UPDATE whale_wallets
            SET enabled = :enabled, updated_at = now()
            WHERE id = :wallet_id
            RETURNING *
            """
        ),
        {"wallet_id": wallet_id, "enabled": enabled},
    ).fetchone()
    if row is None:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="wallet not found")
    db.commit()
    return _row_to_dict(row)


@router.get("/summary", response_model=WalletSummary)
def wallet_summary(db: Session = Depends(get_db)) -> dict[str, int]:
    row = db.execute(
        text(
            """
            SELECT
              (SELECT count(*) FROM whale_wallets) AS total_wallets,
              (SELECT count(*) FROM whale_wallets WHERE enabled = TRUE) AS enabled_wallets,
              (SELECT count(*) FROM whale_wallets WHERE do_not_copy = TRUE) AS do_not_copy_wallets,
              (SELECT count(*) FROM wallet_movements) AS movement_count,
              (SELECT count(*) FROM wallet_movements WHERE manual_review_required = TRUE) AS manual_review_movements
            """
        )
    ).fetchone()
    return _row_to_dict(row)
