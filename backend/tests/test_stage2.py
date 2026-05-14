from datetime import datetime, timezone
from decimal import Decimal

from app.main import app
from app.services.market_data import CoinGeckoPublicMarketDataProvider, DEFAULT_SYMBOL_IDS
from app.services.signal_outcomes import HORIZONS, MockPriceOutcomeProvider, classify_signal_result, price_change_pct
from app.services.wallet_performance import confidence_adjusted_score


def test_stage2_signal_outcome_routes_registered():
    routes = {route.path for route in app.routes}
    assert "/signal-outcomes" in routes
    assert "/signal-outcomes/summary" in routes
    assert "/signal-outcomes/run-once" in routes
    assert "/signal-outcomes/run-due" in routes
    assert "/wallet-performance" in routes


def test_stage2_horizons_match_product_question():
    assert list(HORIZONS.keys()) == ["15m", "1h", "4h", "24h", "7d"]


def test_mock_price_provider_is_deterministic_and_paper_only():
    provider = MockPriceOutcomeProvider()
    movement = {
        "transaction_hash": "0xtx",
        "token_symbol": "ETH",
        "price_at_trade_time": Decimal("100"),
    }
    first = provider.price_for(movement, "1h")
    second = provider.price_for(movement, "1h")
    assert provider.name == "mock"
    assert first == second
    assert first["raw_price_payload"]["paper_trading_only"] is True


def test_signal_result_classification_respects_movement_direction():
    assert classify_signal_result("DEX buy", Decimal("2.0"), 80) == ("favorable", "up")
    assert classify_signal_result("DEX buy", Decimal("-2.0"), 80) == ("unfavorable", "down")
    assert classify_signal_result("DEX sell", Decimal("-2.0"), 80) == ("favorable", "down")
    assert classify_signal_result("DEX buy", Decimal("0.1"), 80) == ("neutral", "flat")
    assert classify_signal_result("DEX buy", Decimal("2.0"), 40) == ("needs_review", "flat")


def test_price_change_pct_handles_missing_and_zero_baseline():
    assert price_change_pct(Decimal("100"), Decimal("110")) == Decimal("10.0")
    assert price_change_pct(None, Decimal("110")) is None
    assert price_change_pct(Decimal("0"), Decimal("110")) is None


def test_public_market_provider_is_read_only_and_allowlisted_without_network_for_unknown_symbol():
    provider = CoinGeckoPublicMarketDataProvider()
    point = provider.price_at_or_after(token_symbol="MOCKUNKNOWN", target_time=datetime.now(timezone.utc))
    assert provider.name == "coingecko_public"
    assert point.price_usd is None
    assert point.paper_trading_only is True
    assert point.source == "unsupported_symbol_allowlist"
    assert "ETH" in DEFAULT_SYMBOL_IDS


def test_wallet_performance_score_is_sample_adjusted_and_bounded():
    small_sample = confidence_adjusted_score(favorable=1, unfavorable=0, total=1, avg_return_pct=Decimal("10"))
    bigger_sample = confidence_adjusted_score(favorable=20, unfavorable=0, total=20, avg_return_pct=Decimal("10"))
    bad_sample = confidence_adjusted_score(favorable=0, unfavorable=20, total=20, avg_return_pct=Decimal("-10"))
    assert Decimal("50") < small_sample < bigger_sample <= Decimal("100")
    assert Decimal("0") <= bad_sample < Decimal("50")
