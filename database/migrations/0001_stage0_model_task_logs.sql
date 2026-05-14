-- Stage 0 foundation migration for model task logging.
-- Apply through Alembic or the selected migration runner when database runtime is available.

CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS model_task_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_type TEXT NOT NULL,
    selected_provider TEXT NOT NULL,
    selected_model TEXT NOT NULL,
    fallback_used BOOLEAN NOT NULL DEFAULT FALSE,
    fallback_reason TEXT,
    status TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_model_task_logs_task_type_created_at
    ON model_task_logs (task_type, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_model_task_logs_fallback_created_at
    ON model_task_logs (fallback_used, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_model_task_logs_provider_created_at
    ON model_task_logs (selected_provider, selected_model, created_at DESC);
