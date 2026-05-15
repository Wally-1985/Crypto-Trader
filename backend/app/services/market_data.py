from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Protocol

import httpx

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings

DEFAULT_SYMBOL_IDS = {
    "BTC": "bitcoin",
    "WBTC": "wrapped-bitcoin",
    "ETH": "ethereum",
    "WETH": "weth",
    "SOL": "solana",
    "BNB": "binancecoin",
    "USDC": "usd-coin",
    "USDT": "tether",
    "DAI": "dai",
    "LINK": "chainlink",
    "UNI": "uniswap",
    "AAVE": "aave",
    "ARB": "arbitrum",
    "OP": "optimism",
    "MATIC": "matic-network",
}


@dataclass(frozen=True)
class PricePoint:
    provider: str
    token_symbol: str
    price_usd: Decimal | None
    observed_at: datetime
    source: str
    paper_trading_only: bool = True
    raw_payload: dict[str, Any] | None = None


class MarketDataRateLimited(RuntimeError):
    def __init__(self, message: str, retry_after_seconds: int | None = None) -> None:
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds


class MarketDataProvider(Protocol):
    name: str

    def price_at_or_after(self, *, token_symbol: str, target_time: datetime) -> PricePoint:
        """Return a read-only USD price for the token near target_time.

        Providers must not trade, place orders, or require frontend/exchange secrets.
        """


class CoinGeckoPublicMarketDataProvider:
    """Read-only public CoinGecko provider for wallet-triggered token outcome checks.

    This is intentionally narrow: wallet-led symbols only, no broad market discovery, no API key committed.
    For now it supports common symbols through a static allowlist and fetches the current public USD price.
    Historical/range pricing can replace this implementation later without changing callers.
    """

    name = "coingecko_public"
    base_url = "https://api.coingecko.com/api/v3"

    def __init__(self, timeout_seconds: float = 10.0) -> None:
        self.timeout_seconds = timeout_seconds

    def coin_id_for_symbol(self, token_symbol: str) -> str | None:
        return DEFAULT_SYMBOL_IDS.get(token_symbol.upper())

    def price_at_or_after(self, *, token_symbol: str, target_time: datetime) -> PricePoint:
        symbol = token_symbol.upper()
        coin_id = self.coin_id_for_symbol(symbol)
        observed_at = datetime.now(timezone.utc)
        if coin_id is None:
            return PricePoint(
                provider=self.name,
                token_symbol=symbol,
                price_usd=None,
                observed_at=observed_at,
                source="unsupported_symbol_allowlist",
                raw_payload={"supported_symbols": sorted(DEFAULT_SYMBOL_IDS), "target_time": target_time.isoformat()},
            )
        return self.price_for_coin_id(token_symbol=symbol, coin_id=coin_id, target_time=target_time)

    def price_for_coin_id(self, *, token_symbol: str, coin_id: str, target_time: datetime) -> PricePoint:
        observed_at = datetime.now(timezone.utc)
        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.get(
                f"{self.base_url}/simple/price",
                params={"ids": coin_id, "vs_currencies": "usd", "include_last_updated_at": "true"},
                headers={"accept": "application/json", "user-agent": f"{settings.app_name}/{settings.app_version}"},
            )
            if response.status_code == 429:
                retry_after = response.headers.get("retry-after")
                raise MarketDataRateLimited(
                    "CoinGecko public API rate limit reached",
                    int(retry_after) if retry_after and retry_after.isdigit() else None,
                )
            response.raise_for_status()
            payload = response.json()

        price = payload.get(coin_id, {}).get("usd")
        last_updated = payload.get(coin_id, {}).get("last_updated_at")
        if last_updated:
            observed_at = datetime.fromtimestamp(int(last_updated), tz=timezone.utc)
        return PricePoint(
            provider=self.name,
            token_symbol=token_symbol.upper(),
            price_usd=Decimal(str(price)) if price is not None else None,
            observed_at=observed_at,
            source="coingecko_simple_price_current_usd",
            raw_payload={"coin_id": coin_id, "target_time": target_time.isoformat(), "response": payload},
        )


def resolve_provider_token_id(db: Session, *, chain: str, token_symbol: str, provider: str, token_contract: str | None = None) -> str | None:
    row = db.execute(
        text(
            """
            SELECT provider_token_id
            FROM token_mappings
            WHERE enabled = TRUE
              AND provider = :provider
              AND chain = :chain
              AND token_symbol = :token_symbol
              AND (token_contract IS NULL OR token_contract = COALESCE(:token_contract, token_contract))
            ORDER BY confidence_score DESC, updated_at DESC
            LIMIT 1
            """
        ),
        {"provider": provider, "chain": chain.lower(), "token_symbol": token_symbol.upper(), "token_contract": token_contract},
    ).fetchone()
    return row._mapping["provider_token_id"] if row else None


class DatabaseBackedCoinGeckoProvider(CoinGeckoPublicMarketDataProvider):
    def __init__(self, db: Session, chain: str, token_contract: str | None = None, timeout_seconds: float = 10.0) -> None:
        super().__init__(timeout_seconds=timeout_seconds)
        self.db = db
        self.chain = chain
        self.token_contract = token_contract

    def coin_id_for_symbol(self, token_symbol: str) -> str | None:
        mapped = resolve_provider_token_id(
            self.db,
            chain=self.chain,
            token_symbol=token_symbol,
            provider=self.name,
            token_contract=self.token_contract,
        )
        return mapped or super().coin_id_for_symbol(token_symbol)

    def price_for_coin_id(self, *, token_symbol: str, coin_id: str, target_time: datetime) -> PricePoint:
        from app.services.market_price_cache import get_cached_price_point, upsert_cached_price_point

        cached = get_cached_price_point(
            self.db,
            provider=self.name,
            provider_token_id=coin_id,
            token_symbol=token_symbol,
            allow_stale=False,
        )
        if cached is not None:
            return cached
        try:
            point = super().price_for_coin_id(token_symbol=token_symbol, coin_id=coin_id, target_time=target_time)
        except MarketDataRateLimited:
            stale = get_cached_price_point(
                self.db,
                provider=self.name,
                provider_token_id=coin_id,
                token_symbol=token_symbol,
                allow_stale=True,
            )
            if stale is not None:
                stale_payload = dict(stale.raw_payload or {})
                stale_payload.update({"rate_limit_fallback": True})
                return PricePoint(
                    provider=stale.provider,
                    token_symbol=stale.token_symbol,
                    price_usd=stale.price_usd,
                    observed_at=stale.observed_at,
                    source=f"{stale.source}_rate_limit_fallback",
                    raw_payload=stale_payload,
                )
            raise
        if point.price_usd is not None:
            upsert_cached_price_point(self.db, provider_token_id=coin_id, price_point=point)
        return point


def market_provider_for_name(name: str) -> MarketDataProvider:
    if name == "coingecko_public":
        return CoinGeckoPublicMarketDataProvider()
    raise ValueError(f"unsupported market data provider: {name}")
