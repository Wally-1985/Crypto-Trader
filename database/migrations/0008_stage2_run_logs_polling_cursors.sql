-- Stage 2 operational run logs and wallet polling cursors.
-- Research/paper-trading only. Stores operational metadata, not secrets.

CREATE TABLE IF NOT EXISTS pipeline_run_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_type TEXT NOT NULL,
    provider TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'started',
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at TIMESTAMPTZ,
    duration_ms INTEGER,
    checked_wallets INTEGER NOT NULL DEFAULT 0,
    checked_movements INTEGER NOT NULL DEFAULT 0,
    fetched_movements INTEGER NOT NULL DEFAULT 0,
    created_movements INTEGER NOT NULL DEFAULT 0,
    enriched_movements INTEGER NOT NULL DEFAULT 0,
    created_outcomes INTEGER NOT NULL DEFAULT 0,
    skipped_duplicates INTEGER NOT NULL DEFAULT 0,
    skipped_existing INTEGER NOT NULL DEFAULT 0,
    provider_errors INTEGER NOT NULL DEFAULT 0,
    skipped_reason TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    paper_trading_only BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT pipeline_run_logs_status_check CHECK (status IN ('started', 'success', 'partial', 'failed', 'skipped')),
    CONSTRAINT pipeline_run_logs_run_type_check CHECK (run_type IN ('wallet_polling', 'movement_enrichment', 'signal_outcomes', 'pipeline'))
);

CREATE INDEX IF NOT EXISTS idx_pipeline_run_logs_started
    ON pipeline_run_logs (started_at DESC);

CREATE INDEX IF NOT EXISTS idx_pipeline_run_logs_type_provider
    ON pipeline_run_logs (run_type, provider, started_at DESC);

CREATE TABLE IF NOT EXISTS wallet_polling_cursors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    wallet_id UUID NOT NULL REFERENCES whale_wallets(id) ON DELETE CASCADE,
    provider TEXT NOT NULL,
    chain TEXT NOT NULL,
    last_seen_block BIGINT,
    last_seen_transaction_time TIMESTAMPTZ,
    last_seen_transaction_hash TEXT,
    last_success_at TIMESTAMPTZ,
    last_error_at TIMESTAMPTZ,
    last_error TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT wallet_polling_cursors_unique_wallet_provider UNIQUE (wallet_id, provider)
);

CREATE INDEX IF NOT EXISTS idx_wallet_polling_cursors_wallet
    ON wallet_polling_cursors (wallet_id, provider);
