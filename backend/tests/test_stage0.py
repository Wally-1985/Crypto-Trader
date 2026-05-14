from app.core.config import settings
from app.core.model_routing import provider_for_task, routing_summary
from app.main import app


def test_live_trading_is_disabled_by_default():
    assert settings.live_trading_enabled is False


def test_low_risk_tasks_route_to_qwen3_4b():
    assert provider_for_task("cleanup") == "ollama:qwen3:4b"
    assert provider_for_task("extraction") == "ollama:qwen3:4b"


def test_health_route_registered():
    routes = {route.path for route in app.routes}
    assert "/health" in routes


def test_routing_summary_has_anthropic_fallback():
    summary = routing_summary()
    assert "anthropic" in summary["fallback_paid_development_model"]
