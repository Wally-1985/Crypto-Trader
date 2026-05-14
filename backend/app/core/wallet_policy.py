from decimal import Decimal

WALLET_TYPES = {
    "Unknown",
    "Whale",
    "Smart Money",
    "VC/Fund",
    "Exchange",
    "Market Maker",
    "Influencer Wallet",
    "Developer Wallet",
    "Suspicious",
    "Do Not Copy",
}

MOVEMENT_TYPES = {
    "DEX buy",
    "DEX sell",
    "CEX deposit",
    "CEX withdrawal",
    "Wallet-to-wallet transfer",
    "Bridge movement",
    "Stablecoin accumulation",
    "Stablecoin deployment",
    "New token position",
    "Position increase",
    "Position reduction",
    "Full exit",
}

MANUAL_REVIEW_WALLET_TYPES = {
    "Unknown",
    "Suspicious",
    "Developer Wallet",
    "Influencer Wallet",
    "Do Not Copy",
}


def normalize_wallet_address(address: str) -> str:
    """Normalize wallet addresses for duplicate prevention.

    EVM-like hexadecimal addresses are lower-cased. Other chains still get
    whitespace trimmed and lower-cased for Stage 1 until chain-specific
    canonicalisation is added.
    """
    return address.strip().lower()


def should_require_manual_review(
    *,
    data_quality_score: int,
    wallet_type: str,
    estimated_usd_value: Decimal | None = None,
    token_contract: str | None = None,
) -> bool:
    if data_quality_score < 70:
        return True
    if wallet_type in MANUAL_REVIEW_WALLET_TYPES:
        return True
    if estimated_usd_value is None or estimated_usd_value <= 0:
        return True
    if not token_contract:
        return True
    return False
