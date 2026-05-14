import pytest

from app.core.config import settings
from app.core.model_routing import (
    PaidModelLimitError,
    provider_for_task,
    route_paid_development_task,
    routing_summary,
    should_fallback_to_anthropic,
)
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
    assert "rate_limit_exceeded" in summary["fallback_trigger_error_codes"]


def test_token_limit_error_triggers_anthropic_fallback():
    calls: list[str] = []

    def primary_call(selection):
        calls.append(selection.provider)
        raise PaidModelLimitError("too many tokens", code="token_limit_exceeded")

    def fallback_call(selection):
        calls.append(selection.provider)
        return {"provider": selection.provider, "model": selection.model}

    result = route_paid_development_task(
        task_type="architecture_reasoning",
        primary_call=primary_call,
        fallback_call=fallback_call,
    )

    assert calls == ["openai", "anthropic"]
    assert result.fallback_used is True
    assert result.selection.provider == "anthropic"
    assert result.log_event.fallback_used is True
    assert result.log_event.status == "fallback_success"
    assert result.log_event.selected_provider == "anthropic"


def test_non_limit_error_does_not_fallback():
    def primary_call(selection):
        raise RuntimeError("invalid request payload")

    def fallback_call(selection):  # pragma: no cover - should not be called
        raise AssertionError("fallback should not run")

    with pytest.raises(RuntimeError):
        route_paid_development_task(
            task_type="architecture_reasoning",
            primary_call=primary_call,
            fallback_call=fallback_call,
        )


def test_should_fallback_to_anthropic_detects_rate_limit_text():
    assert should_fallback_to_anthropic(RuntimeError("rate limit exceeded")) is True
