from dataclasses import dataclass
from decimal import Decimal

from app.core.wallet_policy import MANUAL_REVIEW_WALLET_TYPES, MOVEMENT_TYPES


@dataclass(frozen=True)
class DataQualityResult:
    score: int
    reasons: list[str]
    manual_review_required: bool


def score_wallet_movement(
    *,
    wallet_type: str,
    movement_type: str,
    token_contract: str | None,
    estimated_usd_value: Decimal | None,
    protocol: str | None,
    transaction_hash: str | None,
    transaction_time_present: bool,
    token_symbol: str | None,
) -> DataQualityResult:
    """Score movement quality with explicit, reviewable reasons.

    This is intentionally deterministic. It does not call a model and it does not
    make trading decisions; it only helps route events to review.
    """
    score = 100
    reasons: list[str] = []

    if wallet_type in MANUAL_REVIEW_WALLET_TYPES:
        score -= 25
        reasons.append(f"wallet_type_requires_review:{wallet_type}")
    if movement_type not in MOVEMENT_TYPES:
        score -= 30
        reasons.append("unsupported_movement_type")
    if not token_contract:
        score -= 15
        reasons.append("missing_token_contract")
    if estimated_usd_value is None or estimated_usd_value <= 0:
        score -= 20
        reasons.append("missing_or_nonpositive_usd_value")
    if not protocol:
        score -= 8
        reasons.append("missing_protocol")
    if not transaction_hash:
        score -= 12
        reasons.append("missing_transaction_hash")
    if not transaction_time_present:
        score -= 10
        reasons.append("missing_transaction_time")
    if not token_symbol:
        score -= 8
        reasons.append("missing_token_symbol")

    score = max(0, min(100, score))
    manual_review_required = score < 70 or any(
        reason.startswith("wallet_type_requires_review") for reason in reasons
    )
    if manual_review_required and "manual_review_threshold_triggered" not in reasons:
        reasons.append("manual_review_threshold_triggered")

    return DataQualityResult(score=score, reasons=reasons, manual_review_required=manual_review_required)
