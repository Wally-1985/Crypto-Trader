from decimal import Decimal

from app.main import app
from app.services.signal_outcomes import HORIZONS, MockPriceOutcomeProvider, classify_signal_result


def test_stage2_signal_outcome_routes_registered():
    routes = {route.path for route in app.routes}
    assert "/signal-outcomes" in routes
    assert "/signal-outcomes/summary" in routes
    assert "/signal-outcomes/run-once" in routes


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
