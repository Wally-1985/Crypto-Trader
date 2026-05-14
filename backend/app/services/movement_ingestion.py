import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.data_quality import score_wallet_movement
from app.core.wallet_policy import should_require_manual_review


def _row_to_dict(row: Any) -> dict[str, Any]:
    return dict(row._mapping)


def load_wallet(db: Session, wallet_id: UUID) -> dict[str, Any] | None:
    row = db.execute(
        text(
            """
            SELECT id, wallet_type, alert_threshold_usd, enabled, chain, normalized_address
            FROM whale_wallets
            WHERE id = :wallet_id
            """
        ),
        {"wallet_id": wallet_id},
    ).fetchone()
    return _row_to_dict(row) if row else None


def ingest_wallet_movement(db: Session, payload: dict[str, Any], *, commit: bool = True) -> tuple[dict[str, Any] | None, bool]:
    """Validate, score, dedupe, store and alert for one movement payload.

    Returns (movement, created). Duplicate movements are skipped without error.
    Caller owns rollback for unexpected exceptions.
    """
    wallet = load_wallet(db, payload["wallet_id"])
    if wallet is None:
        raise ValueError("wallet not found")

    quality = score_wallet_movement(
        wallet_type=wallet["wallet_type"],
        movement_type=payload["movement_type"],
        token_contract=payload.get("token_contract"),
        estimated_usd_value=payload.get("estimated_usd_value"),
        protocol=payload.get("protocol"),
        transaction_hash=payload.get("transaction_hash"),
        transaction_time_present=bool(payload.get("transaction_time")),
        token_symbol=payload.get("token_symbol"),
    )
    manual_review_required = quality.manual_review_required or should_require_manual_review(
        data_quality_score=quality.score,
        wallet_type=wallet["wallet_type"],
        estimated_usd_value=payload.get("estimated_usd_value"),
        token_contract=payload.get("token_contract"),
    )
    alert_threshold_crossed = bool(
        payload.get("estimated_usd_value") is not None
        and payload["estimated_usd_value"] >= wallet["alert_threshold_usd"]
    )

    values = {
        "wallet_id": payload["wallet_id"],
        "chain": payload["chain"],
        "transaction_hash": payload["transaction_hash"],
        "movement_type": payload["movement_type"],
        "token_symbol": payload["token_symbol"].upper(),
        "token_contract": payload.get("token_contract"),
        "token_amount": payload.get("token_amount"),
        "estimated_usd_value": payload.get("estimated_usd_value"),
        "from_address": payload.get("from_address"),
        "to_address": payload.get("to_address"),
        "protocol": payload.get("protocol"),
        "block_number": payload.get("block_number"),
        "transaction_time": payload.get("transaction_time") or datetime.now(timezone.utc),
        "price_at_trade_time": payload.get("price_at_trade_time"),
        "gas_fee": payload.get("gas_fee"),
        "alert_threshold_crossed": alert_threshold_crossed,
        "processed_by_agent": payload.get("processed_by_agent", False),
        "data_quality_score": quality.score,
        "manual_review_required": manual_review_required,
        "raw_api_payload_json": json.dumps(payload.get("raw_api_payload", {}), default=str),
        "data_quality_reasons_json": json.dumps(quality.reasons),
    }

    try:
        row = db.execute(
            text(
                """
                INSERT INTO wallet_movements (
                    wallet_id, chain, transaction_hash, movement_type, token_symbol, token_contract,
                    token_amount, estimated_usd_value, from_address, to_address, protocol, block_number,
                    transaction_time, price_at_trade_time, gas_fee, alert_threshold_crossed, processed_by_agent,
                    data_quality_score, manual_review_required, raw_api_payload, data_quality_reasons
                ) VALUES (
                    :wallet_id, :chain, :transaction_hash, :movement_type, :token_symbol, :token_contract,
                    :token_amount, :estimated_usd_value, :from_address, :to_address, :protocol, :block_number,
                    :transaction_time, :price_at_trade_time, :gas_fee, :alert_threshold_crossed, :processed_by_agent,
                    :data_quality_score, :manual_review_required, CAST(:raw_api_payload_json AS jsonb),
                    CAST(:data_quality_reasons_json AS jsonb)
                )
                RETURNING *
                """
            ),
            values,
        ).fetchone()
    except IntegrityError:
        db.rollback()
        return None, False

    if alert_threshold_crossed:
        candidate_decision = "manual_review" if manual_review_required else "watch"
        title = f"Large {values['movement_type']} detected: {values['token_symbol']}"
        message = (
            f"Wallet movement crossed the configured alert threshold of {wallet['alert_threshold_usd']} USD. "
            "Review before any paper-trade decision."
        )
        db.execute(
            text(
                """
                INSERT INTO agent_alerts (
                    wallet_id, wallet_movement_id, alert_type, severity, title, message,
                    data_quality_score, manual_review_required, decision_snapshot, status, candidate_decision
                ) VALUES (
                    :wallet_id, :wallet_movement_id, 'large_wallet_movement', 'review', :title, :message,
                    :data_quality_score, :manual_review_required, CAST(:decision_snapshot AS jsonb),
                    'open', :candidate_decision
                )
                """
            ),
            {
                "wallet_id": payload["wallet_id"],
                "wallet_movement_id": row._mapping["id"],
                "title": title,
                "message": message,
                "data_quality_score": quality.score,
                "manual_review_required": manual_review_required,
                "candidate_decision": candidate_decision,
                "decision_snapshot": json.dumps(
                    {
                        "paper_trading_only": True,
                        "alert_threshold_usd": str(wallet["alert_threshold_usd"]),
                        "estimated_usd_value": str(payload.get("estimated_usd_value")),
                        "manual_review_required": manual_review_required,
                        "data_quality_score": quality.score,
                        "data_quality_reasons": quality.reasons,
                    }
                ),
            },
        )
    if commit:
        db.commit()
    return _row_to_dict(row), True


def decimal_or_none(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    return Decimal(str(value))
