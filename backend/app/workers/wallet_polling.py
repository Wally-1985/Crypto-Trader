from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Protocol

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.movement_ingestion import ingest_wallet_movement


class WalletMovementProvider(Protocol):
    """Provider interface for future chain/indexer integrations.

    Implementations must not require committed API keys and must treat all
    external payloads as untrusted input.
    """

    name: str

    def fetch_movements(self, wallet: dict) -> list[dict]:
        """Return untrusted movement payloads for one wallet."""


@dataclass(frozen=True)
class DryRunWalletMovementProvider:
    name: str = "dry_run"

    def fetch_movements(self, wallet: dict) -> list[dict]:
        return []


@dataclass(frozen=True)
class MockWalletMovementProvider:
    """Deterministic provider for testing the full ingestion loop safely."""

    name: str = "mock"

    def fetch_movements(self, wallet: dict) -> list[dict]:
        short_wallet = str(wallet["id"]).replace("-", "")[:16]
        tx_hash = f"mock-{wallet['chain']}-{short_wallet}-stage1"
        threshold = Decimal(str(wallet["alert_threshold_usd"] or 0))
        estimated_value = max(threshold + Decimal("1000"), Decimal("25000"))
        return [
            {
                "wallet_id": wallet["id"],
                "chain": wallet["chain"],
                "transaction_hash": tx_hash,
                "movement_type": "DEX buy",
                "token_symbol": "MOCK",
                "token_contract": "0xmocktoken000000000000000000000000000000000000",
                "token_amount": Decimal("1000"),
                "estimated_usd_value": estimated_value,
                "from_address": wallet["normalized_address"],
                "to_address": "0xmockliquiditypool00000000000000000000000000",
                "protocol": "MockSwap",
                "transaction_time": datetime(2026, 5, 14, 10, 55, tzinfo=timezone.utc),
                "processed_by_agent": True,
                "raw_api_payload": {
                    "source": "mock_provider",
                    "paper_trading_only": True,
                    "deterministic": True,
                },
            }
        ]


def provider_for_name(name: str | None) -> WalletMovementProvider:
    if name == "mock":
        return MockWalletMovementProvider()
    return DryRunWalletMovementProvider()


def run_wallet_polling_once(db: Session, provider: WalletMovementProvider | None = None) -> dict:
    """Check enabled wallets through a provider, then validate/score/dedupe/store/alert."""
    active_provider = provider or DryRunWalletMovementProvider()
    rows = db.execute(
        text(
            """
            SELECT id, chain, normalized_address, wallet_type, alert_threshold_usd
            FROM whale_wallets
            WHERE enabled = TRUE AND do_not_copy = FALSE
            ORDER BY watch_priority ASC, updated_at DESC
            """
        )
    ).fetchall()
    wallets = [dict(row._mapping) for row in rows]
    created_movements = 0
    skipped_duplicates = 0
    fetched_movements = 0

    for wallet in wallets:
        for movement_payload in active_provider.fetch_movements(wallet):
            fetched_movements += 1
            movement, created = ingest_wallet_movement(db, movement_payload, commit=False)
            if created and movement is not None:
                created_movements += 1
            else:
                skipped_duplicates += 1
    db.commit()

    return {
        "provider": active_provider.name,
        "checked_wallets": len(wallets),
        "eligible_wallets": len(wallets),
        "fetched_movements": fetched_movements,
        "created_movements": created_movements,
        "skipped_duplicates": skipped_duplicates,
        "skipped_reason": "dry_run_provider_has_no_external_integration" if active_provider.name == "dry_run" else None,
        "paper_trading_only": True,
    }
