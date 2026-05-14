import json
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.wallet_policy import should_require_manual_review
from app.db.session import get_db
from app.schemas.wallets import WalletMovement, WalletMovementCreate

router = APIRouter(prefix="/wallet-movements", tags=["wallet-movements"])


def _row_to_dict(row: Any) -> dict[str, Any]:
    return dict(row._mapping)


def _load_wallet(db: Session, wallet_id: UUID) -> dict[str, Any]:
    row = db.execute(
        text(
            """
            SELECT id, wallet_type, alert_threshold_usd, enabled
            FROM whale_wallets
            WHERE id = :wallet_id
            """
        ),
        {"wallet_id": wallet_id},
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="wallet not found")
    return _row_to_dict(row)


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
    wallet = _load_wallet(db, payload.wallet_id)
    alert_threshold_crossed = bool(
        payload.estimated_usd_value is not None
        and payload.estimated_usd_value >= wallet["alert_threshold_usd"]
    )
    manual_review_required = should_require_manual_review(
        data_quality_score=payload.data_quality_score,
        wallet_type=wallet["wallet_type"],
        estimated_usd_value=payload.estimated_usd_value,
        token_contract=payload.token_contract,
    )

    values = payload.model_dump()
    values["token_symbol"] = payload.token_symbol.upper()
    values["alert_threshold_crossed"] = alert_threshold_crossed
    values["manual_review_required"] = manual_review_required
    values["raw_api_payload_json"] = json.dumps(payload.raw_api_payload)

    try:
        row = db.execute(
            text(
                """
                INSERT INTO wallet_movements (
                    wallet_id,
                    chain,
                    transaction_hash,
                    movement_type,
                    token_symbol,
                    token_contract,
                    token_amount,
                    estimated_usd_value,
                    from_address,
                    to_address,
                    protocol,
                    block_number,
                    transaction_time,
                    price_at_trade_time,
                    gas_fee,
                    alert_threshold_crossed,
                    processed_by_agent,
                    data_quality_score,
                    manual_review_required,
                    raw_api_payload
                ) VALUES (
                    :wallet_id,
                    :chain,
                    :transaction_hash,
                    :movement_type,
                    :token_symbol,
                    :token_contract,
                    :token_amount,
                    :estimated_usd_value,
                    :from_address,
                    :to_address,
                    :protocol,
                    :block_number,
                    :transaction_time,
                    :price_at_trade_time,
                    :gas_fee,
                    :alert_threshold_crossed,
                    :processed_by_agent,
                    :data_quality_score,
                    :manual_review_required,
                    CAST(:raw_api_payload_json AS jsonb)
                )
                RETURNING *
                """
            ),
            values,
        ).fetchone()

        if alert_threshold_crossed:
            title = f"Large {values['movement_type']} detected: {values['token_symbol']}"
            message = (
                f"Wallet movement crossed the configured alert threshold "
                f"of {wallet['alert_threshold_usd']} USD. Review before any paper-trade decision."
            )
            db.execute(
                text(
                    """
                    INSERT INTO agent_alerts (
                        wallet_id,
                        wallet_movement_id,
                        alert_type,
                        severity,
                        title,
                        message,
                        data_quality_score,
                        manual_review_required,
                        decision_snapshot
                    ) VALUES (
                        :wallet_id,
                        :wallet_movement_id,
                        'large_wallet_movement',
                        'review',
                        :title,
                        :message,
                        :data_quality_score,
                        TRUE,
                        CAST(:decision_snapshot AS jsonb)
                    )
                    """
                ),
                {
                    "wallet_id": payload.wallet_id,
                    "wallet_movement_id": row._mapping["id"],
                    "title": title,
                    "message": message,
                    "data_quality_score": payload.data_quality_score,
                    "decision_snapshot": json.dumps(
                        {
                            "paper_trading_only": True,
                            "alert_threshold_usd": str(wallet["alert_threshold_usd"]),
                            "estimated_usd_value": str(payload.estimated_usd_value),
                            "manual_review_required": True,
                        }
                    ),
                },
            )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="movement already exists for this wallet/transaction or violates movement policy",
        ) from exc

    return _row_to_dict(row)
