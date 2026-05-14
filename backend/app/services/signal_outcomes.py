import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

HORIZONS: dict[str, timedelta] = {
    "15m": timedelta(minutes=15),
    "1h": timedelta(hours=1),
    "4h": timedelta(hours=4),
    "24h": timedelta(hours=24),
    "7d": timedelta(days=7),
}
BUYISH_MOVEMENTS = {"DEX buy", "CEX withdrawal", "Stablecoin deployment", "New token position", "Position increase"}
SELLISH_MOVEMENTS = {"DEX sell", "CEX deposit", "Stablecoin accumulation", "Position reduction", "Full exit"}


@dataclass(frozen=True)
class OutcomeRunSummary:
    provider: str
    checked_movements: int
    created_outcomes: int
    skipped_existing: int
    paper_trading_only: bool = True


def _row_to_dict(row: Any) -> dict[str, Any]:
    return dict(row._mapping)


class MockPriceOutcomeProvider:
    """Deterministic Stage 2 provider for validating outcome plumbing without external market data."""

    name = "mock"

    def price_for(self, movement: dict[str, Any], horizon: str) -> dict[str, Any]:
        baseline = Decimal(str(movement.get("price_at_trade_time") or "100"))
        seed = sum(ord(char) for char in f"{movement['transaction_hash']}:{horizon}:{movement['token_symbol']}")
        basis_points = Decimal((seed % 1201) - 600) / Decimal("100")
        if horizon in {"24h", "7d"}:
            basis_points *= Decimal("1.5")
        change_pct = basis_points / Decimal("100")
        outcome_price = baseline * (Decimal("1") + change_pct)
        return {
            "baseline_price": baseline,
            "outcome_price": outcome_price,
            "price_change_pct": change_pct * Decimal("100"),
            "raw_price_payload": {
                "provider": self.name,
                "deterministic": True,
                "paper_trading_only": True,
                "seed": seed,
            },
        }


def classify_signal_result(movement_type: str, price_change_pct: Decimal | None, data_quality_score: int) -> tuple[str, str]:
    if price_change_pct is None or data_quality_score < 50:
        return "needs_review", "flat"
    if price_change_pct > Decimal("0.25"):
        direction = "up"
    elif price_change_pct < Decimal("-0.25"):
        direction = "down"
    else:
        return "neutral", "flat"

    if movement_type in BUYISH_MOVEMENTS:
        return ("favorable" if direction == "up" else "unfavorable"), direction
    if movement_type in SELLISH_MOVEMENTS:
        return ("favorable" if direction == "down" else "unfavorable"), direction
    return "needs_review", direction


def list_signal_outcomes(
    db: Session,
    *,
    wallet_id: Any | None = None,
    token_symbol: str | None = None,
    horizon: str | None = None,
    signal_result: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    filters: list[str] = []
    params: dict[str, Any] = {"limit": limit}
    if wallet_id is not None:
        filters.append("wallet_id = :wallet_id")
        params["wallet_id"] = wallet_id
    if token_symbol is not None:
        filters.append("token_symbol = :token_symbol")
        params["token_symbol"] = token_symbol.upper()
    if horizon is not None:
        filters.append("horizon = :horizon")
        params["horizon"] = horizon
    if signal_result is not None:
        filters.append("signal_result = :signal_result")
        params["signal_result"] = signal_result
    where_clause = "WHERE " + " AND ".join(filters) if filters else ""
    rows = db.execute(
        text(
            f"""
            SELECT *
            FROM signal_outcomes
            {where_clause}
            ORDER BY created_at DESC
            LIMIT :limit
            """
        ),
        params,
    ).fetchall()
    return [_row_to_dict(row) for row in rows]


def summarize_signal_outcomes(db: Session) -> dict[str, Any]:
    row = db.execute(
        text(
            """
            SELECT
                COUNT(*)::int AS total_outcomes,
                COUNT(*) FILTER (WHERE signal_result = 'favorable')::int AS favorable_outcomes,
                COUNT(*) FILTER (WHERE signal_result = 'unfavorable')::int AS unfavorable_outcomes,
                COUNT(*) FILTER (WHERE signal_result = 'neutral')::int AS neutral_outcomes,
                COUNT(*) FILTER (WHERE signal_result = 'needs_review')::int AS needs_review_outcomes
            FROM signal_outcomes
            """
        )
    ).fetchone()
    return _row_to_dict(row) if row else {"total_outcomes": 0, "favorable_outcomes": 0, "unfavorable_outcomes": 0, "neutral_outcomes": 0, "needs_review_outcomes": 0}


def run_mock_outcome_backfill(db: Session, *, limit: int = 50, commit: bool = True) -> OutcomeRunSummary:
    provider = MockPriceOutcomeProvider()
    rows = db.execute(
        text(
            """
            SELECT wm.*
            FROM wallet_movements wm
            ORDER BY wm.transaction_time DESC, wm.created_at DESC
            LIMIT :limit
            """
        ),
        {"limit": limit},
    ).fetchall()
    checked = 0
    created = 0
    skipped = 0
    now = datetime.now(timezone.utc)
    for row in rows:
        movement = _row_to_dict(row)
        checked += 1
        for horizon, delta in HORIZONS.items():
            prices = provider.price_for(movement, horizon)
            signal_result, direction = classify_signal_result(
                movement["movement_type"], prices["price_change_pct"], int(movement["data_quality_score"])
            )
            inserted = db.execute(
                text(
                    """
                    INSERT INTO signal_outcomes (
                        wallet_movement_id, wallet_id, chain, token_symbol, horizon, provider,
                        baseline_price, outcome_price, price_change_pct, direction, signal_result,
                        measured_at, due_at, data_quality_score, paper_trading_only, raw_price_payload
                    ) VALUES (
                        :wallet_movement_id, :wallet_id, :chain, :token_symbol, :horizon, :provider,
                        :baseline_price, :outcome_price, :price_change_pct, :direction, :signal_result,
                        :measured_at, :due_at, :data_quality_score, TRUE, CAST(:raw_price_payload AS jsonb)
                    )
                    ON CONFLICT (wallet_movement_id, horizon, provider) DO NOTHING
                    RETURNING id
                    """
                ),
                {
                    "wallet_movement_id": movement["id"],
                    "wallet_id": movement["wallet_id"],
                    "chain": movement["chain"],
                    "token_symbol": movement["token_symbol"].upper(),
                    "horizon": horizon,
                    "provider": provider.name,
                    "baseline_price": prices["baseline_price"],
                    "outcome_price": prices["outcome_price"],
                    "price_change_pct": prices["price_change_pct"],
                    "direction": direction,
                    "signal_result": signal_result,
                    "measured_at": now,
                    "due_at": movement["transaction_time"] + delta,
                    "data_quality_score": movement["data_quality_score"],
                    "raw_price_payload": json.dumps(prices["raw_price_payload"]),
                },
            ).fetchone()
            if inserted:
                created += 1
            else:
                skipped += 1
    if commit:
        db.commit()
    return OutcomeRunSummary(provider=provider.name, checked_movements=checked, created_outcomes=created, skipped_existing=skipped)
