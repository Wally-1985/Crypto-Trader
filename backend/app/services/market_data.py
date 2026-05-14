from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Protocol

import httpx

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

        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.get(
                f"{self.base_url}/simple/price",
                params={"ids": coin_id, "vs_currencies": "usd", "include_last_updated_at": "true"},
                headers={"accept": "application/json", "user-agent": f"{settings.app_name}/{settings.app_version}"},
            )
            response.raise_for_status()
            payload = response.json()

        price = payload.get(coin_id, {}).get("usd")
        last_updated = payload.get(coin_id, {}).get("last_updated_at")
        if last_updated:
            observed_at = datetime.fromtimestamp(int(last_updated), tz=timezone.utc)
        return PricePoint(
            provider=self.name,
            token_symbol=symbol,
            price_usd=Decimal(str(price)) if price is not None else None,
            observed_at=observed_at,
            source="coingecko_simple_price_current_usd",
            raw_payload={"coin_id": coin_id, "target_time": target_time.isoformat(), "response": payload},
        )


def market_provider_for_name(name: str) -> MarketDataProvider:
    if name == "coingecko_public":
        return CoinGeckoPublicMarketDataProvider()
    raise ValueError(f"unsupported market data provider: {name}")
