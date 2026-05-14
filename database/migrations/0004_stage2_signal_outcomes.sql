-- Stage 2 foundation for price outcomes and signal validation.
-- V1 remains research and paper-trading only. No live trading execution or exchange credentials are introduced.

CREATE TABLE IF NOT EXISTS signal_outcomes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    wallet_movement_id UUID NOT NULL REFERENCES wallet_movements(id) ON DELETE CASCADE,
    wallet_id UUID NOT NULL REFERENCES whale_wallets(id) ON DELETE CASCADE,
    chain TEXT NOT NULL,
    token_symbol TEXT NOT NULL,
    horizon TEXT NOT NULL,
    provider TEXT NOT NULL DEFAULT 'mock',
    baseline_price NUMERIC(30, 12),
    outcome_price NUMERIC(30, 12),
    price_change_pct NUMERIC(12, 6),
    direction TEXT NOT NULL DEFAULT 'flat',
    signal_result TEXT NOT NULL DEFAULT 'needs_review',
    measured_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    due_at TIMESTAMPTZ NOT NULL,
    data_quality_score INTEGER NOT NULL DEFAULT 0,
    paper_trading_only BOOLEAN NOT NULL DEFAULT TRUE,
    raw_price_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT signal_outcomes_horizon_check CHECK (horizon IN ('15m', '1h', '4h', '24h', '7d')),
    CONSTRAINT signal_outcomes_direction_check CHECK (direction IN ('up', 'down', 'flat')),
    CONSTRAINT signal_outcomes_result_check CHECK (signal_result IN ('favorable', 'unfavorable', 'neutral', 'needs_review')),
    CONSTRAINT signal_outcomes_quality_check CHECK (data_quality_score BETWEEN 0 AND 100),
    CONSTRAINT signal_outcomes_paper_only_check CHECK (paper_trading_only = TRUE),
    CONSTRAINT signal_outcomes_unique_movement_horizon_provider UNIQUE (wallet_movement_id, horizon, provider)
);

CREATE INDEX IF NOT EXISTS idx_signal_outcomes_wallet_created
    ON signal_outcomes (wallet_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_signal_outcomes_token_horizon
    ON signal_outcomes (chain, token_symbol, horizon, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_signal_outcomes_result_horizon
    ON signal_outcomes (signal_result, horizon, created_at DESC);
