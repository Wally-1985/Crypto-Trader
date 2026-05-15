import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.market_data import PricePoint

DEFAULT_PRICE_CACHE_TTL = timedelta(minutes=10)
STALE_PRICE_GRACE = timedelta(hours=6)


def get_cached_price_point(
    db: Session,
    *,
    provider: str,
    provider_token_id: str,
    token_symbol: str,
    allow_stale: bool = False,
    now: datetime | None = None,
) -> PricePoint | None:
    now = now or datetime.now(timezone.utc)
    stale_cutoff = now - STALE_PRICE_GRACE
    row = db.execute(
        text(
            """
            SELECT provider, provider_token_id, price_usd, observed_at, expires_at, source, raw_payload
            FROM market_price_cache
            WHERE provider = :provider
              AND provider_token_id = :provider_token_id
              AND vs_currency = 'usd'
              AND (:allow_stale OR expires_at > :now)
              AND (NOT :allow_stale OR observed_at >= :stale_cutoff)
            ORDER BY expires_at DESC
            LIMIT 1
            """
        ),
        {
            "provider": provider,
            "provider_token_id": provider_token_id,
            "allow_stale": allow_stale,
            "now": now,
            "stale_cutoff": stale_cutoff,
        },
    ).fetchone()
    if row is None:
        return None
    data = row._mapping
    raw_payload = dict(data["raw_payload"] or {})
    raw_payload.update({"provider_token_id": provider_token_id, "cache_hit": True, "cache_stale": data["expires_at"] <= now})
    return PricePoint(
        provider=provider,
        token_symbol=token_symbol.upper(),
        price_usd=Decimal(str(data["price_usd"])) if data["price_usd"] is not None else None,
        observed_at=data["observed_at"],
        source=f"{data['source']}_cache" if not str(data["source"]).endswith("_cache") else data["source"],
        raw_payload=raw_payload,
    )


def upsert_cached_price_point(
    db: Session,
    *,
    provider_token_id: str,
    price_point: PricePoint,
    ttl: timedelta = DEFAULT_PRICE_CACHE_TTL,
) -> None:
    now = datetime.now(timezone.utc)
    expires_at = now + ttl
    db.execute(
        text(
            """
            INSERT INTO market_price_cache (
                provider, provider_token_id, vs_currency, price_usd, observed_at, expires_at, source, raw_payload
            ) VALUES (
                :provider, :provider_token_id, 'usd', :price_usd, :observed_at, :expires_at, :source, CAST(:raw_payload AS jsonb)
            )
            ON CONFLICT (provider, provider_token_id, vs_currency)
            DO UPDATE SET
                price_usd = EXCLUDED.price_usd,
                observed_at = EXCLUDED.observed_at,
                expires_at = EXCLUDED.expires_at,
                source = EXCLUDED.source,
                raw_payload = EXCLUDED.raw_payload,
                updated_at = now()
            """
        ),
        {
            "provider": price_point.provider,
            "provider_token_id": provider_token_id,
            "price_usd": price_point.price_usd,
            "observed_at": price_point.observed_at,
            "expires_at": expires_at,
            "source": price_point.source,
            "raw_payload": json.dumps(price_point.raw_payload or {}, default=str),
        },
    )
