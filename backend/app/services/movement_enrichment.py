import json
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.market_data import DatabaseBackedCoinGeckoProvider, resolve_provider_token_id


@dataclass(frozen=True)
class MovementEnrichmentSummary:
    provider: str
    checked_movements: int
    enriched_movements: int
    skipped_unmapped: int
    provider_errors: int
    paper_trading_only: bool = True


def classify_protocol_and_type(movement: dict[str, Any]) -> tuple[str | None, str | None, int, list[str]]:
    payload = movement.get("raw_api_payload") or {}
    function_name = str((payload.get("payload") or {}).get("functionName") or "").lower()
    token_symbol = str(movement.get("token_symbol") or "").upper()
    current_protocol = movement.get("protocol")
    current_type = movement.get("movement_type")
    reasons: list[str] = []
    source_confidence = 70

    if "supply(" in function_name and ("AAVE" in token_symbol or token_symbol.startswith("AETH")):
        reasons.append("aave_receipt_token_supply_detected")
        return "Aave supply receipt token", "Position increase", 85, reasons
    if "supply(" in function_name:
        reasons.append("aave_supply_underlying_token_detected")
        return "Aave supply", "Stablecoin deployment" if token_symbol in {"USDC", "USDT", "DAI"} else "Position reduction", 85, reasons
    if "withdraw(" in function_name:
        reasons.append("aave_withdraw_detected")
        return "Aave withdrawal", "Stablecoin accumulation" if token_symbol in {"USDC", "USDT", "DAI"} else "Position increase", 85, reasons
    if "transfer(" in function_name:
        reasons.append("erc20_transfer_detected")
        return current_protocol, current_type, 75, reasons
    return current_protocol, current_type, source_confidence, reasons


def list_enrichment_candidates(db: Session, *, limit: int) -> list[dict[str, Any]]:
    rows = db.execute(
        text(
            """
            SELECT *
            FROM wallet_movements
            WHERE raw_api_payload->>'source' = 'etherscan_readonly'
              AND (
                estimated_usd_value IS NULL
                OR price_at_trade_time IS NULL
                OR raw_api_payload->>'enriched_by' IS NULL
                OR (token_symbol LIKE 'AETH%' AND protocol <> 'Aave supply receipt token')
              )
            ORDER BY transaction_time DESC, created_at DESC
            LIMIT :limit
            """
        ),
        {"limit": limit},
    ).fetchall()
    return [dict(row._mapping) for row in rows]


def run_movement_enrichment(db: Session, *, provider_name: str = "coingecko_public", limit: int = 100, commit: bool = True) -> MovementEnrichmentSummary:
    provider = DatabaseBackedCoinGeckoProvider(db, chain="ethereum")
    checked = 0
    enriched = 0
    skipped_unmapped = 0
    provider_errors = 0
    now = datetime.now(timezone.utc)
    price_cache = {}

    for movement in list_enrichment_candidates(db, limit=limit):
        checked += 1
        token_symbol = movement["token_symbol"].upper()
        token_contract = movement.get("token_contract")
        coin_id = resolve_provider_token_id(
            db,
            chain=movement["chain"],
            token_symbol=token_symbol,
            provider=provider_name,
            token_contract=token_contract,
        ) or provider.coin_id_for_symbol(token_symbol)
        protocol, movement_type, source_confidence, classification_reasons = classify_protocol_and_type(movement)
        if coin_id is None:
            skipped_unmapped += 1
            raw_payload = dict(movement.get("raw_api_payload") or {})
            raw_payload.update(
                {
                    "enriched_by": "movement_enrichment",
                    "enrichment_provider": provider_name,
                    "enrichment_status": "skipped_unmapped_token",
                    "source_confidence": source_confidence,
                    "classification_reasons": classification_reasons,
                    "enriched_at": now.isoformat(),
                    "paper_trading_only": True,
                }
            )
            db.execute(
                text("UPDATE wallet_movements SET protocol = :protocol, movement_type = :movement_type, raw_api_payload = CAST(:raw_payload AS jsonb), updated_at = now() WHERE id = :id"),
                {"id": movement["id"], "protocol": protocol, "movement_type": movement_type, "raw_payload": json.dumps(raw_payload, default=str)},
            )
            continue
        try:
            cache_key = (provider_name, coin_id)
            if cache_key not in price_cache:
                price_cache[cache_key] = provider.price_for_coin_id(token_symbol=token_symbol, coin_id=coin_id, target_time=movement["transaction_time"])
            price = price_cache[cache_key]
        except Exception:
            provider_errors += 1
            continue
        estimated_usd = None
        if price.price_usd is not None and movement.get("token_amount") is not None:
            estimated_usd = (Decimal(str(movement["token_amount"])) * price.price_usd).quantize(Decimal("0.01"))
        raw_payload = dict(movement.get("raw_api_payload") or {})
        raw_payload.update(
            {
                "enriched_by": "movement_enrichment",
                "enrichment_provider": provider_name,
                "enrichment_status": "enriched" if estimated_usd is not None else "price_missing",
                "provider_token_id": coin_id,
                "price_source": price.source,
                "price_observed_at": price.observed_at.isoformat(),
                "source_confidence": source_confidence,
                "classification_reasons": classification_reasons,
                "enriched_at": now.isoformat(),
                "paper_trading_only": True,
            }
        )
        db.execute(
            text(
                """
                UPDATE wallet_movements
                SET estimated_usd_value = COALESCE(:estimated_usd_value, estimated_usd_value),
                    price_at_trade_time = COALESCE(:price_at_trade_time, price_at_trade_time),
                    protocol = :protocol,
                    movement_type = :movement_type,
                    manual_review_required = TRUE,
                    raw_api_payload = CAST(:raw_payload AS jsonb),
                    updated_at = now()
                WHERE id = :id
                """
            ),
            {
                "id": movement["id"],
                "estimated_usd_value": estimated_usd,
                "price_at_trade_time": price.price_usd,
                "protocol": protocol,
                "movement_type": movement_type,
                "raw_payload": json.dumps(raw_payload, default=str),
            },
        )
        enriched += 1
    if commit:
        db.commit()
    return MovementEnrichmentSummary(
        provider=provider_name,
        checked_movements=checked,
        enriched_movements=enriched,
        skipped_unmapped=skipped_unmapped,
        provider_errors=provider_errors,
    )
