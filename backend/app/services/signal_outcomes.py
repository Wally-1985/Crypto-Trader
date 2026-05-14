import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.market_data import MarketDataProvider, PricePoint, market_provider_for_name

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
    checked_due_outcomes: int = 0
    skipped_not_due: int = 0
    provider_errors: int = 0
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
    provider: str | None = None,
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
    if provider is not None:
        filters.append("provider = :provider")
        params["provider"] = provider
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


def insert_signal_outcome(
    db: Session,
    *,
    movement: dict[str, Any],
    horizon: str,
    provider: str,
    baseline_price: Decimal | None,
    outcome_price: Decimal | None,
    price_change_pct: Decimal | None,
    measured_at: datetime,
    due_at: datetime,
    raw_price_payload: dict[str, Any],
) -> bool:
    signal_result, direction = classify_signal_result(movement["movement_type"], price_change_pct, int(movement["data_quality_score"]))
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
            "provider": provider,
            "baseline_price": baseline_price,
            "outcome_price": outcome_price,
            "price_change_pct": price_change_pct,
            "direction": direction,
            "signal_result": signal_result,
            "measured_at": measured_at,
            "due_at": due_at,
            "data_quality_score": movement["data_quality_score"],
            "raw_price_payload": json.dumps(raw_price_payload, default=str),
        },
    ).fetchone()
    return inserted is not None


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
            due_at = movement["transaction_time"] + delta
            if insert_signal_outcome(
                db,
                movement=movement,
                horizon=horizon,
                provider=provider.name,
                baseline_price=prices["baseline_price"],
                outcome_price=prices["outcome_price"],
                price_change_pct=prices["price_change_pct"],
                measured_at=now,
                due_at=due_at,
                raw_price_payload=prices["raw_price_payload"],
            ):
                created += 1
            else:
                skipped += 1
    if commit:
        db.commit()
    return OutcomeRunSummary(provider=provider.name, checked_movements=checked, created_outcomes=created, skipped_existing=skipped)


def price_change_pct(baseline_price: Decimal | None, outcome_price: Decimal | None) -> Decimal | None:
    if baseline_price is None or outcome_price is None or baseline_price <= 0:
        return None
    return ((outcome_price - baseline_price) / baseline_price) * Decimal("100")


def build_real_provider_payload(
    *,
    provider: MarketDataProvider,
    movement: dict[str, Any],
    horizon: str,
    due_at: datetime,
) -> tuple[Decimal | None, Decimal | None, Decimal | None, datetime, dict[str, Any]]:
    baseline = movement.get("price_at_trade_time")
    baseline_price = Decimal(str(baseline)) if baseline is not None else None
    price_point: PricePoint = provider.price_at_or_after(token_symbol=movement["token_symbol"], target_time=due_at)
    change = price_change_pct(baseline_price, price_point.price_usd)
    raw_payload = {
        "provider": price_point.provider,
        "source": price_point.source,
        "paper_trading_only": price_point.paper_trading_only,
        "target_due_at": due_at.isoformat(),
        "observed_at": price_point.observed_at.isoformat(),
        "note": "Read-only market data lookup. No orders or live trades are executed.",
        "payload": price_point.raw_payload or {},
    }
    return baseline_price, price_point.price_usd, change, price_point.observed_at, raw_payload


def run_due_outcome_backfill(
    db: Session,
    *,
    provider_name: str = "mock",
    limit: int = 50,
    commit: bool = True,
    now: datetime | None = None,
) -> OutcomeRunSummary:
    now = now or datetime.now(timezone.utc)
    real_provider = market_provider_for_name(provider_name) if provider_name != "mock" else None
    mock_provider = MockPriceOutcomeProvider() if provider_name == "mock" else None
    rows = db.execute(
        text(
            """
            SELECT wm.*
            FROM wallet_movements wm
            ORDER BY wm.transaction_time ASC, wm.created_at ASC
            LIMIT :limit
            """
        ),
        {"limit": limit},
    ).fetchall()
    checked_movements = 0
    checked_due_outcomes = 0
    created = 0
    skipped_existing = 0
    skipped_not_due = 0
    provider_errors = 0

    for row in rows:
        movement = _row_to_dict(row)
        checked_movements += 1
        for horizon, delta in HORIZONS.items():
            due_at = movement["transaction_time"] + delta
            if due_at > now:
                skipped_not_due += 1
                continue
            checked_due_outcomes += 1
            if mock_provider is not None:
                prices = mock_provider.price_for(movement, horizon)
                baseline_price = prices["baseline_price"]
                outcome_price = prices["outcome_price"]
                change = prices["price_change_pct"]
                measured_at = now
                raw_payload = prices["raw_price_payload"] | {"due_only_worker": True, "target_due_at": due_at.isoformat()}
            else:
                try:
                    baseline_price, outcome_price, change, measured_at, raw_payload = build_real_provider_payload(
                        provider=real_provider, movement=movement, horizon=horizon, due_at=due_at
                    )
                except Exception as exc:  # provider/network errors are recorded as needs-review outcomes
                    provider_errors += 1
                    baseline_price = Decimal(str(movement["price_at_trade_time"])) if movement.get("price_at_trade_time") is not None else None
                    outcome_price = None
                    change = None
                    measured_at = now
                    raw_payload = {
                        "provider": provider_name,
                        "paper_trading_only": True,
                        "target_due_at": due_at.isoformat(),
                        "error": str(exc),
                    }
            if insert_signal_outcome(
                db,
                movement=movement,
                horizon=horizon,
                provider=provider_name,
                baseline_price=baseline_price,
                outcome_price=outcome_price,
                price_change_pct=change,
                measured_at=measured_at,
                due_at=due_at,
                raw_price_payload=raw_payload,
            ):
                created += 1
            else:
                skipped_existing += 1
    if commit:
        db.commit()
    return OutcomeRunSummary(
        provider=provider_name,
        checked_movements=checked_movements,
        created_outcomes=created,
        skipped_existing=skipped_existing,
        checked_due_outcomes=checked_due_outcomes,
        skipped_not_due=skipped_not_due,
        provider_errors=provider_errors,
    )
