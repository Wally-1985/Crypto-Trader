from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from app.core.config import settings
from app.core.model_task_logs import ModelTaskLogEvent, build_model_task_log_event

LOW_RISK_LOCAL_TASKS = {
    "cleanup",
    "classification",
    "extraction",
    "tagging",
    "first_pass_summary",
}

FALLBACK_TRIGGER_ERROR_CODES = {
    "context_length_exceeded",
    "rate_limit_exceeded",
    "token_limit_exceeded",
    "insufficient_quota",
}


class PaidModelLimitError(RuntimeError):
    """Raised when a paid provider is blocked by token/rate/quota limits."""

    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class ModelProviderSelection:
    provider: str
    model: str
    reason: str

    @property
    def label(self) -> str:
        return f"{self.provider}:{self.model}"


@dataclass(frozen=True)
class ModelRouteResult:
    selection: ModelProviderSelection
    fallback_used: bool
    fallback_reason: str | None
    log_event: ModelTaskLogEvent
    response: Any = None


def primary_paid_selection() -> ModelProviderSelection:
    return ModelProviderSelection(
        provider=settings.primary_paid_provider,
        model=settings.primary_development_model,
        reason="primary_paid_development_provider",
    )


def fallback_paid_selection() -> ModelProviderSelection:
    return ModelProviderSelection(
        provider=settings.fallback_paid_provider,
        model=settings.fallback_development_model,
        reason="fallback_paid_development_provider",
    )


def local_ollama_selection() -> ModelProviderSelection:
    return ModelProviderSelection(
        provider="ollama",
        model=settings.ollama_model,
        reason="low_risk_local_task",
    )


def selection_for_task(task_type: str) -> ModelProviderSelection:
    """Return configured provider selection without calling a model."""
    normalized = task_type.strip().lower()
    if settings.ollama_enabled and normalized in LOW_RISK_LOCAL_TASKS:
        return local_ollama_selection()
    if settings.paid_model_escalation_enabled:
        return primary_paid_selection()
    return ModelProviderSelection(
        provider="manual_review_required",
        model="none",
        reason="paid_escalation_disabled",
    )


def provider_for_task(task_type: str) -> str:
    """Return configured provider label for a task without executing model output.

    Stage 0 only establishes routing policy. It does not call paid providers or
    allow model output to execute commands, trade, or modify security settings.
    """
    return selection_for_task(task_type).label


def should_fallback_to_anthropic(error: BaseException) -> bool:
    """True when ChatGPT/OpenAI failed due to token, context, rate or quota limits."""
    code = getattr(error, "code", None)
    if isinstance(code, str) and code in FALLBACK_TRIGGER_ERROR_CODES:
        return True

    message = str(error).lower()
    return any(
        marker in message
        for marker in (
            "context length",
            "context_length",
            "rate limit",
            "rate_limit",
            "token limit",
            "token_limit",
            "too many tokens",
            "insufficient quota",
            "quota",
        )
    )


def route_paid_development_task(
    *,
    task_type: str,
    primary_call: Callable[[ModelProviderSelection], Any],
    fallback_call: Callable[[ModelProviderSelection], Any],
) -> ModelRouteResult:
    """Call primary paid provider and gracefully fall back to Anthropic on limit errors.

    The callables are injected so Stage 0 can test routing with mocks. Provider
    clients must never expose API keys to frontend code or logs.
    """
    primary = primary_paid_selection()
    try:
        response = primary_call(primary)
        return ModelRouteResult(
            selection=primary,
            fallback_used=False,
            fallback_reason=None,
            response=response,
            log_event=build_model_task_log_event(
                task_type=task_type,
                selected_provider=primary.provider,
                selected_model=primary.model,
                fallback_used=False,
                fallback_reason=None,
                status="success",
            ),
        )
    except Exception as exc:
        if not should_fallback_to_anthropic(exc):
            raise

        fallback = fallback_paid_selection()
        response = fallback_call(fallback)
        return ModelRouteResult(
            selection=fallback,
            fallback_used=True,
            fallback_reason=getattr(exc, "code", None) or str(exc),
            response=response,
            log_event=build_model_task_log_event(
                task_type=task_type,
                selected_provider=fallback.provider,
                selected_model=fallback.model,
                fallback_used=True,
                fallback_reason=getattr(exc, "code", None) or str(exc),
                status="fallback_success",
                metadata={"primary_provider": primary.provider, "primary_model": primary.model},
            ),
        )


def fallback_provider() -> str:
    return fallback_paid_selection().label


def routing_summary() -> dict[str, object]:
    return {
        "low_risk_local_model": local_ollama_selection().label,
        "low_risk_task_types": sorted(LOW_RISK_LOCAL_TASKS),
        "primary_paid_development_model": primary_paid_selection().label,
        "fallback_paid_development_model": fallback_provider(),
        "fallback_trigger_error_codes": sorted(FALLBACK_TRIGGER_ERROR_CODES),
        "production_reasoning_model": settings.production_reasoning_model,
        "live_trading_enabled": settings.live_trading_enabled,
    }
