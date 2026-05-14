from decimal import Decimal

import pytest

from app.core.wallet_policy import normalize_wallet_address, should_require_manual_review
from app.main import app
from app.schemas.wallets import WhaleWalletCreate, WalletMovementCreate


def test_stage1_wallet_routes_registered():
    routes = {route.path for route in app.routes}
    assert "/wallets" in routes
    assert "/wallets/summary" in routes


def test_frontend_cors_origin_configured():
    middleware_names = {middleware.cls.__name__ for middleware in app.user_middleware}
    assert "CORSMiddleware" in middleware_names


def test_wallet_address_normalisation_prevents_case_duplicates():
    assert normalize_wallet_address("  0xABCDEF1234  ") == "0xabcdef1234"


def test_do_not_copy_wallet_cannot_be_copy_trade_enabled():
    with pytest.raises(ValueError):
        WhaleWalletCreate(
            wallet_address="0xabc",
            chain="ethereum",
            do_not_copy=True,
            copy_trade_enabled=True,
        )


def test_stage1_wallet_type_policy_accepts_expected_types():
    wallet = WhaleWalletCreate(
        wallet_address="0xabc",
        chain="ethereum",
        wallet_type="Smart Money",
        alert_threshold_usd=Decimal("250000"),
    )
    assert wallet.wallet_type == "Smart Money"
    assert wallet.normalized_address == "0xabc"


def test_stage1_movement_type_policy_accepts_expected_types():
    movement = WalletMovementCreate(
        wallet_id="00000000-0000-0000-0000-000000000001",
        chain="ethereum",
        transaction_hash="0xtx",
        movement_type="DEX buy",
        token_symbol="ETH",
        transaction_time="2026-05-14T00:00:00Z",
        data_quality_score=80,
    )
    assert movement.movement_type == "DEX buy"
    assert movement.manual_review_required is True


def test_manual_review_required_for_low_quality_or_risky_wallet_types():
    assert should_require_manual_review(
        data_quality_score=69,
        wallet_type="Whale",
        estimated_usd_value=Decimal("100000"),
        token_contract="0xtoken",
    ) is True
    assert should_require_manual_review(
        data_quality_score=90,
        wallet_type="Suspicious",
        estimated_usd_value=Decimal("100000"),
        token_contract="0xtoken",
    ) is True
    assert should_require_manual_review(
        data_quality_score=90,
        wallet_type="Whale",
        estimated_usd_value=Decimal("100000"),
        token_contract="0xtoken",
    ) is False
