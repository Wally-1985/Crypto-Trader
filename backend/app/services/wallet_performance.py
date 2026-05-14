from decimal import Decimal
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


def _row_to_dict(row: Any) -> dict[str, Any]:
    return dict(row._mapping)


def _decimal(value: Any) -> Decimal:
    return Decimal(str(value or 0))


def confidence_adjusted_score(*, favorable: int, unfavorable: int, total: int, avg_return_pct: Decimal) -> Decimal:
    """Rank wallets without over-trusting tiny samples.

    50 is neutral. Win/loss edge and average return can move the score, but the
    sample factor caps early confidence until more outcomes accumulate.
    """
    decisive = favorable + unfavorable
    if decisive == 0 or total == 0:
        return Decimal("50.00")
    edge = (Decimal(favorable - unfavorable) / Decimal(decisive)) * Decimal("100")
    sample_factor = min(Decimal(total) / Decimal("20"), Decimal("1"))
    raw = Decimal("50") + (edge * Decimal("0.35") * sample_factor) + (avg_return_pct * Decimal("0.15") * sample_factor)
    return max(Decimal("0"), min(Decimal("100"), raw.quantize(Decimal("0.01"))))


def list_wallet_performance(
    db: Session,
    *,
    provider: str | None = None,
    horizon: str | None = None,
    min_outcomes: int = 0,
    limit: int = 100,
) -> list[dict[str, Any]]:
    filters = []
    params: dict[str, Any] = {"limit": limit, "min_outcomes": min_outcomes}
    if provider:
        filters.append("so.provider = :provider")
        params["provider"] = provider
    if horizon:
        filters.append("so.horizon = :horizon")
        params["horizon"] = horizon
    outcome_filter = " AND " + " AND ".join(filters) if filters else ""

    rows = db.execute(
        text(
            f"""
            SELECT
                ww.id AS wallet_id,
                ww.label,
                ww.normalized_address,
                ww.chain,
                ww.wallet_type,
                ww.watch_priority,
                COUNT(so.id)::int AS total_outcomes,
                COUNT(*) FILTER (WHERE so.signal_result = 'favorable')::int AS favorable_outcomes,
                COUNT(*) FILTER (WHERE so.signal_result = 'unfavorable')::int AS unfavorable_outcomes,
                COUNT(*) FILTER (WHERE so.signal_result = 'neutral')::int AS neutral_outcomes,
                COUNT(*) FILTER (WHERE so.signal_result = 'needs_review')::int AS needs_review_outcomes,
                COALESCE(AVG(so.price_change_pct) FILTER (WHERE so.price_change_pct IS NOT NULL), 0)::numeric(12, 4) AS avg_return_pct,
                COALESCE(AVG(so.data_quality_score) FILTER (WHERE so.id IS NOT NULL), 0)::numeric(8, 2) AS avg_data_quality_score,
                MAX(so.created_at) AS last_outcome_at
            FROM whale_wallets ww
            LEFT JOIN signal_outcomes so
                ON so.wallet_id = ww.id
                {outcome_filter}
            GROUP BY ww.id, ww.label, ww.normalized_address, ww.chain, ww.wallet_type, ww.watch_priority
            HAVING COUNT(so.id) >= :min_outcomes
            ORDER BY COUNT(so.id) DESC, ww.watch_priority ASC, ww.updated_at DESC
            LIMIT :limit
            """
        ),
        params,
    ).fetchall()

    rankings: list[dict[str, Any]] = []
    for row in rows:
        item = _row_to_dict(row)
        decisive = item["favorable_outcomes"] + item["unfavorable_outcomes"]
        item["win_rate_pct"] = (
            (Decimal(item["favorable_outcomes"]) / Decimal(decisive) * Decimal("100")).quantize(Decimal("0.01"))
            if decisive
            else Decimal("0.00")
        )
        item["confidence_score"] = confidence_adjusted_score(
            favorable=item["favorable_outcomes"],
            unfavorable=item["unfavorable_outcomes"],
            total=item["total_outcomes"],
            avg_return_pct=_decimal(item["avg_return_pct"]),
        )
        item["paper_trading_only"] = True
        rankings.append(item)

    rankings.sort(
        key=lambda item: (
            item["total_outcomes"] > 0,
            item["confidence_score"],
            item["total_outcomes"],
            _decimal(item["avg_return_pct"]),
        ),
        reverse=True,
    )
    return rankings
