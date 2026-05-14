from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Protocol

import httpx
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.movement_ingestion import ingest_wallet_movement


class WalletMovementProvider(Protocol):
    """Provider interface for wallet-led read-only movement ingestion.

    Implementations must not sign transactions, hold private keys, place orders,
    scan broad markets, or trust external payloads without normalization.
    """

    name: str

    def fetch_movements(self, wallet: dict) -> list[dict]:
        """Return untrusted movement payloads for one watched wallet."""


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


@dataclass(frozen=True)
class EtherscanReadOnlyMovementProvider:
    """Read-only Ethereum watched-wallet provider using Etherscan account APIs.

    Requires ETHERSCAN_API_KEY. If no key is configured, it returns no movements and
    records a skipped reason in the polling summary. No private keys or signing APIs
    are used.
    """

    api_key: str = settings.etherscan_api_key
    base_url: str = settings.etherscan_base_url
    max_transactions: int = settings.etherscan_max_transactions_per_wallet
    name: str = "etherscan_readonly"

    def configured(self) -> bool:
        return bool(self.api_key)

    def fetch_movements(self, wallet: dict) -> list[dict]:
        if not self.configured() or wallet["chain"] != "ethereum":
            return []
        address = wallet["normalized_address"]
        native = self._fetch_account_action(address, "txlist")
        token = self._fetch_account_action(address, "tokentx")
        movements: list[dict] = []
        for item in native[: self.max_transactions]:
            movement = self._normalize_native_transfer(wallet, item)
            if movement is not None:
                movements.append(movement)
        for item in token[: self.max_transactions]:
            movement = self._normalize_token_transfer(wallet, item)
            if movement is not None:
                movements.append(movement)
        return movements[: self.max_transactions]

    def _fetch_account_action(self, address: str, action: str) -> list[dict[str, Any]]:
        params = {
            "module": "account",
            "action": action,
            "address": address,
            "startblock": 0,
            "endblock": 99999999,
            "page": 1,
            "offset": self.max_transactions,
            "sort": "desc",
            "apikey": self.api_key,
        }
        with httpx.Client(timeout=settings.etherscan_timeout_seconds) as client:
            response = client.get(self.base_url, params=params)
            response.raise_for_status()
            payload = response.json()
        result = payload.get("result", [])
        return result if isinstance(result, list) else []

    def _normalize_native_transfer(self, wallet: dict, item: dict[str, Any]) -> dict[str, Any] | None:
        value_wei = Decimal(str(item.get("value") or "0"))
        if value_wei <= 0:
            return None
        amount = value_wei / Decimal("1000000000000000000")
        wallet_address = wallet["normalized_address"].lower()
        from_address = str(item.get("from") or "").lower()
        to_address = str(item.get("to") or "").lower()
        movement_type = "CEX withdrawal" if to_address == wallet_address else "CEX deposit" if from_address == wallet_address else "Wallet-to-wallet transfer"
        timestamp = datetime.fromtimestamp(int(item.get("timeStamp") or 0), tz=timezone.utc)
        return {
            "wallet_id": wallet["id"],
            "chain": wallet["chain"],
            "transaction_hash": item.get("hash") or f"etherscan-native-{wallet['id']}-{item.get('blockNumber')}",
            "movement_type": movement_type,
            "token_symbol": "ETH",
            "token_contract": None,
            "token_amount": amount,
            "estimated_usd_value": None,
            "from_address": item.get("from"),
            "to_address": item.get("to"),
            "protocol": "Etherscan account txlist",
            "block_number": int(item.get("blockNumber") or 0),
            "transaction_time": timestamp,
            "gas_fee": self._gas_fee_eth(item),
            "processed_by_agent": True,
            "raw_api_payload": self._raw_payload("native", item),
        }

    def _normalize_token_transfer(self, wallet: dict, item: dict[str, Any]) -> dict[str, Any] | None:
        raw_value = Decimal(str(item.get("value") or "0"))
        decimals = int(item.get("tokenDecimal") or 0)
        amount = raw_value / (Decimal(10) ** decimals) if decimals > 0 else raw_value
        if amount <= 0:
            return None
        wallet_address = wallet["normalized_address"].lower()
        from_address = str(item.get("from") or "").lower()
        to_address = str(item.get("to") or "").lower()
        if to_address == wallet_address:
            movement_type = "Position increase"
        elif from_address == wallet_address:
            movement_type = "Position reduction"
        else:
            movement_type = "Wallet-to-wallet transfer"
        timestamp = datetime.fromtimestamp(int(item.get("timeStamp") or 0), tz=timezone.utc)
        return {
            "wallet_id": wallet["id"],
            "chain": wallet["chain"],
            "transaction_hash": item.get("hash") or f"etherscan-token-{wallet['id']}-{item.get('blockNumber')}",
            "movement_type": movement_type,
            "token_symbol": str(item.get("tokenSymbol") or "UNKNOWN")[:32],
            "token_contract": item.get("contractAddress"),
            "token_amount": amount,
            "estimated_usd_value": None,
            "from_address": item.get("from"),
            "to_address": item.get("to"),
            "protocol": "Etherscan account tokentx",
            "block_number": int(item.get("blockNumber") or 0),
            "transaction_time": timestamp,
            "gas_fee": self._gas_fee_eth(item),
            "processed_by_agent": True,
            "raw_api_payload": self._raw_payload("erc20", item),
        }

    def _gas_fee_eth(self, item: dict[str, Any]) -> Decimal | None:
        gas_used = item.get("gasUsed") or item.get("gas")
        gas_price = item.get("gasPrice")
        if gas_used is None or gas_price is None:
            return None
        return (Decimal(str(gas_used)) * Decimal(str(gas_price))) / Decimal("1000000000000000000")

    def _raw_payload(self, transfer_type: str, item: dict[str, Any]) -> dict[str, Any]:
        return {
            "source": self.name,
            "provider": "etherscan",
            "transfer_type": transfer_type,
            "paper_trading_only": True,
            "read_only": True,
            "unsupported_token_warning": "Set a token mapping if this symbol/contract cannot resolve to market data.",
            "payload": item,
        }


def provider_for_name(name: str | None) -> WalletMovementProvider:
    if name == "mock":
        return MockWalletMovementProvider()
    if name == "etherscan_readonly":
        return EtherscanReadOnlyMovementProvider()
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
    provider_errors = 0

    for wallet in wallets:
        try:
            movement_payloads = active_provider.fetch_movements(wallet)
        except Exception:
            provider_errors += 1
            continue
        for movement_payload in movement_payloads:
            fetched_movements += 1
            movement, created = ingest_wallet_movement(db, movement_payload, commit=False)
            if created and movement is not None:
                created_movements += 1
            else:
                skipped_duplicates += 1
    db.commit()

    skipped_reason = None
    if active_provider.name == "dry_run":
        skipped_reason = "dry_run_provider_has_no_external_integration"
    elif active_provider.name == "etherscan_readonly" and hasattr(active_provider, "configured") and not active_provider.configured():
        skipped_reason = "etherscan_api_key_not_configured"

    return {
        "provider": active_provider.name,
        "checked_wallets": len(wallets),
        "eligible_wallets": len(wallets),
        "fetched_movements": fetched_movements,
        "created_movements": created_movements,
        "skipped_duplicates": skipped_duplicates,
        "skipped_reason": skipped_reason,
        "provider_errors": provider_errors,
        "paper_trading_only": True,
    }
