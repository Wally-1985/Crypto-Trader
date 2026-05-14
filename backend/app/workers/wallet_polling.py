from dataclasses import dataclass
from typing import Protocol

from sqlalchemy import text
from sqlalchemy.orm import Session


class WalletMovementProvider(Protocol):
    """Provider interface for future chain/indexer integrations.

    Implementations must not require committed API keys and must treat all
    external payloads as untrusted input. Stage 1 ships a dry-run provider only.
    """

    name: str

    def fetch_movements(self, wallet: dict) -> list[dict]:
        """Return untrusted movement payloads for one wallet."""


@dataclass(frozen=True)
class DryRunWalletMovementProvider:
    name: str = "dry_run"

    def fetch_movements(self, wallet: dict) -> list[dict]:
        return []


def run_wallet_polling_once(db: Session, provider: WalletMovementProvider | None = None) -> dict:
    """Check enabled wallets through a provider skeleton.

    The Stage 1 default is intentionally dry-run only: it proves orchestration,
    counts eligible wallets, and leaves ingestion to explicit provider work later.
    """
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
    for wallet in wallets:
        movements = active_provider.fetch_movements(wallet)
        # Real providers will validate, score, dedupe and insert through the movement service path.
        created_movements += len(movements)

    return {
        "provider": active_provider.name,
        "checked_wallets": len(wallets),
        "eligible_wallets": len(wallets),
        "created_movements": created_movements,
        "skipped_reason": "dry_run_provider_has_no_external_integration" if active_provider.name == "dry_run" else None,
        "paper_trading_only": True,
    }
