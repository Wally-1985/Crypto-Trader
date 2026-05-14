from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class ModelTaskLogEvent:
    """Stage 0 model task log event shape.

    This defines what will be persisted to the future `model_task_logs` table.
    It deliberately does not store prompts, raw responses, API keys, or secrets.
    """

    event_id: str
    task_type: str
    selected_provider: str
    selected_model: str
    fallback_used: bool
    fallback_reason: str | None
    status: str
    created_at: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def safe_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_model_task_log_event(
    *,
    task_type: str,
    selected_provider: str,
    selected_model: str,
    fallback_used: bool,
    fallback_reason: str | None,
    status: str,
    metadata: dict[str, Any] | None = None,
) -> ModelTaskLogEvent:
    return ModelTaskLogEvent(
        event_id=str(uuid4()),
        task_type=task_type,
        selected_provider=selected_provider,
        selected_model=selected_model,
        fallback_used=fallback_used,
        fallback_reason=fallback_reason,
        status=status,
        created_at=datetime.now(UTC).isoformat(),
        metadata=metadata or {},
    )
