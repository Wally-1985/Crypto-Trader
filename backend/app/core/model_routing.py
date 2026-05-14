from app.core.config import settings

LOW_RISK_LOCAL_TASKS = {
    "cleanup",
    "classification",
    "extraction",
    "tagging",
    "first_pass_summary",
}


def provider_for_task(task_type: str) -> str:
    """Return configured provider for a task without executing any model output.

    Stage 0 only establishes routing policy. It does not call paid providers or
    allow model output to execute commands, trade, or modify security settings.
    """
    normalized = task_type.strip().lower()
    if settings.ollama_enabled and normalized in LOW_RISK_LOCAL_TASKS:
        return f"ollama:{settings.ollama_model}"
    if settings.paid_model_escalation_enabled:
        return f"{settings.primary_paid_provider}:{settings.primary_development_model}"
    return "manual_review_required"


def fallback_provider() -> str:
    return f"{settings.fallback_paid_provider}:{settings.fallback_development_model}"


def routing_summary() -> dict[str, object]:
    return {
        "low_risk_local_model": f"ollama:{settings.ollama_model}",
        "low_risk_task_types": sorted(LOW_RISK_LOCAL_TASKS),
        "primary_paid_development_model": f"{settings.primary_paid_provider}:{settings.primary_development_model}",
        "fallback_paid_development_model": fallback_provider(),
        "production_reasoning_model": settings.production_reasoning_model,
        "live_trading_enabled": settings.live_trading_enabled,
    }
