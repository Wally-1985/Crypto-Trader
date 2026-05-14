import json
from dataclasses import dataclass
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from app.core.config import settings
from app.core.model_task_logs import ModelTaskLogEvent, build_model_task_log_event


@dataclass(frozen=True)
class OllamaHealth:
    reachable: bool
    required_model: str
    model_available: bool
    installed_models: list[str]
    error: str | None = None


class OllamaUnavailableError(RuntimeError):
    """Raised when the local Ollama API is not reachable or qwen3:4b is missing."""


def _assert_local_ollama_policy() -> None:
    parsed = urlparse(settings.ollama_base_url)
    allowed_hosts = {"localhost", "127.0.0.1", "::1"}
    if parsed.scheme != "http" or parsed.hostname not in allowed_hosts:
        raise OllamaUnavailableError("Ollama base URL must be local-only HTTP")
    if settings.ollama_model != "qwen3:4b":
        raise OllamaUnavailableError("Project policy allows only qwen3:4b for local Ollama")


def _request_json(path: str, payload: dict | None = None, timeout_seconds: int = 30) -> dict:
    _assert_local_ollama_policy()
    url = settings.ollama_base_url.rstrip("/") + path
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="GET" if payload is None else "POST",
    )
    with urlopen(request, timeout=timeout_seconds) as response:  # nosec B310 - base URL is local config by policy
        return json.loads(response.read().decode("utf-8"))


def check_ollama_health() -> OllamaHealth:
    """Check local Ollama and confirm the only approved local model is available."""
    try:
        tags = _request_json("/api/tags", timeout_seconds=5)
    except (OllamaUnavailableError, OSError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        return OllamaHealth(
            reachable=False,
            required_model=settings.ollama_model,
            model_available=False,
            installed_models=[],
            error=str(exc),
        )

    models = sorted(model.get("name", "") for model in tags.get("models", []) if model.get("name"))
    return OllamaHealth(
        reachable=True,
        required_model=settings.ollama_model,
        model_available=settings.ollama_model in models,
        installed_models=models,
    )


def run_low_risk_ollama_prompt(task_type: str, prompt: str) -> tuple[str, ModelTaskLogEvent]:
    """Run a low-risk local prompt through qwen3:4b and return a safe log event.

    Do not pass secrets, private keys, seed phrases, withdrawal keys, or scraped
    instructions that could trigger tool execution. Model output is treated as
    untrusted text and must never execute commands, trades, or security changes.
    """
    health = check_ollama_health()
    if not health.reachable:
        raise OllamaUnavailableError(f"Ollama API unavailable: {health.error}")
    if not health.model_available:
        raise OllamaUnavailableError(f"Required local model missing: {settings.ollama_model}")

    response = _request_json(
        "/api/generate",
        payload={"model": settings.ollama_model, "prompt": prompt, "stream": False},
        timeout_seconds=60,
    )
    text = str(response.get("response", ""))
    event = build_model_task_log_event(
        task_type=task_type,
        selected_provider="ollama",
        selected_model=settings.ollama_model,
        fallback_used=False,
        fallback_reason=None,
        status="success",
        metadata={"local_only": True},
    )
    return text, event
