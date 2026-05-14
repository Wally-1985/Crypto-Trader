from decimal import Decimal

import pytest

from app.core.data_quality import score_wallet_movement
from app.core.wallet_policy import normalize_wallet_address, should_require_manual_review
from app.main import app
from app.schemas.wallets import WhaleWalletCreate, WhaleWalletUpdate, WalletMovementCreate
from app.workers.wallet_polling import DryRunWalletMovementProvider, MockWalletMovementProvider


def test_stage1_wallet_routes_registered():
    routes = {route.path for route in app.routes}
    assert "/wallets" in routes
    assert "/wallets/summary" in routes
    assert "/wallets/{wallet_id}" in routes
    assert "/wallet-movements" in routes
    assert "/agent-alerts" in routes
    assert "/wallet-polling/run-once" in routes


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
    with pytest.raises(ValueError):
        WhaleWalletUpdate(do_not_copy=True, copy_trade_enabled=True)


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


def test_dry_run_polling_provider_is_safe_default():
    provider = DryRunWalletMovementProvider()
    assert provider.name == "dry_run"
    assert provider.fetch_movements({"normalized_address": "0xabc"}) == []


def test_mock_provider_returns_deterministic_safe_payload():
    provider = MockWalletMovementProvider()
    movements = provider.fetch_movements(
        {
            "id": "00000000-0000-0000-0000-000000000001",
            "chain": "ethereum",
            "normalized_address": "0xabc",
            "alert_threshold_usd": Decimal("1000"),
        }
    )
    assert provider.name == "mock"
    assert movements[0]["transaction_hash"] == "mock-ethereum-0000000000000000-stage1"
    assert movements[0]["raw_api_payload"]["paper_trading_only"] is True


def test_data_quality_scoring_explains_manual_review():
    result = score_wallet_movement(
        wallet_type="Unknown",
        movement_type="DEX buy",
        token_contract=None,
        estimated_usd_value=None,
        protocol=None,
        transaction_hash="0xtx",
        transaction_time_present=True,
        token_symbol="ETH",
    )
    assert result.score < 70
    assert result.manual_review_required is True
    assert "missing_token_contract" in result.reasons
    assert "missing_or_nonpositive_usd_value" in result.reasons


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
