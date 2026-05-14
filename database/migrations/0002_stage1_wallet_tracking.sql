-- Stage 1 foundation migration for whale wallet database and movement tracking.
-- V1 remains research and paper-trading only. No private keys, seed phrases, or live trading keys are stored.

CREATE TABLE IF NOT EXISTS whale_wallets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    wallet_address TEXT NOT NULL,
    normalized_address TEXT NOT NULL,
    chain TEXT NOT NULL,
    label TEXT,
    wallet_type TEXT NOT NULL DEFAULT 'Unknown',
    notes TEXT,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    alert_threshold_usd NUMERIC(20, 2) NOT NULL DEFAULT 100000,
    watch_priority INTEGER NOT NULL DEFAULT 3,
    confidence_weighting NUMERIC(5, 2) NOT NULL DEFAULT 1.00,
    copy_trade_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    do_not_copy BOOLEAN NOT NULL DEFAULT FALSE,
    last_seen_at TIMESTAMPTZ,
    tags TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    sectors_of_interest TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT whale_wallets_wallet_type_check CHECK (wallet_type IN (
        'Unknown',
        'Whale',
        'Smart Money',
        'VC/Fund',
        'Exchange',
        'Market Maker',
        'Influencer Wallet',
        'Developer Wallet',
        'Suspicious',
        'Do Not Copy'
    )),
    CONSTRAINT whale_wallets_watch_priority_check CHECK (watch_priority BETWEEN 1 AND 5),
    CONSTRAINT whale_wallets_confidence_weighting_check CHECK (confidence_weighting >= 0 AND confidence_weighting <= 5),
    CONSTRAINT whale_wallets_alert_threshold_check CHECK (alert_threshold_usd >= 0),
    CONSTRAINT whale_wallets_do_not_copy_disables_copy CHECK (do_not_copy = FALSE OR copy_trade_enabled = FALSE),
    CONSTRAINT whale_wallets_chain_address_unique UNIQUE (chain, normalized_address)
);

CREATE INDEX IF NOT EXISTS idx_whale_wallets_enabled_priority
    ON whale_wallets (enabled, watch_priority, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_whale_wallets_chain_type
    ON whale_wallets (chain, wallet_type);

CREATE TABLE IF NOT EXISTS watchlist (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    wallet_id UUID NOT NULL REFERENCES whale_wallets(id) ON DELETE CASCADE,
    watch_reason TEXT NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_watchlist_wallet_enabled
    ON watchlist (wallet_id, enabled, created_at DESC);

CREATE TABLE IF NOT EXISTS wallet_movements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    wallet_id UUID NOT NULL REFERENCES whale_wallets(id) ON DELETE CASCADE,
    chain TEXT NOT NULL,
    transaction_hash TEXT NOT NULL,
    movement_type TEXT NOT NULL,
    token_symbol TEXT NOT NULL,
    token_contract TEXT,
    token_amount NUMERIC(38, 18),
    estimated_usd_value NUMERIC(20, 2),
    from_address TEXT,
    to_address TEXT,
    protocol TEXT,
    block_number BIGINT,
    transaction_time TIMESTAMPTZ NOT NULL,
    price_at_trade_time NUMERIC(30, 12),
    gas_fee NUMERIC(30, 12),
    alert_threshold_crossed BOOLEAN NOT NULL DEFAULT FALSE,
    processed_by_agent BOOLEAN NOT NULL DEFAULT FALSE,
    data_quality_score INTEGER NOT NULL DEFAULT 0,
    manual_review_required BOOLEAN NOT NULL DEFAULT TRUE,
    raw_api_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT wallet_movements_movement_type_check CHECK (movement_type IN (
        'DEX buy',
        'DEX sell',
        'CEX deposit',
        'CEX withdrawal',
        'Wallet-to-wallet transfer',
        'Bridge movement',
        'Stablecoin accumulation',
        'Stablecoin deployment',
        'New token position',
        'Position increase',
        'Position reduction',
        'Full exit'
    )),
    CONSTRAINT wallet_movements_data_quality_score_check CHECK (data_quality_score BETWEEN 0 AND 100),
    CONSTRAINT wallet_movements_unique_tx_wallet UNIQUE (wallet_id, chain, transaction_hash, movement_type, token_symbol)
);

CREATE INDEX IF NOT EXISTS idx_wallet_movements_wallet_time
    ON wallet_movements (wallet_id, transaction_time DESC);

CREATE INDEX IF NOT EXISTS idx_wallet_movements_chain_token_time
    ON wallet_movements (chain, token_symbol, transaction_time DESC);

CREATE INDEX IF NOT EXISTS idx_wallet_movements_alert_review
    ON wallet_movements (alert_threshold_crossed, manual_review_required, transaction_time DESC);

CREATE INDEX IF NOT EXISTS idx_wallet_movements_raw_payload_gin
    ON wallet_movements USING GIN (raw_api_payload);

CREATE TABLE IF NOT EXISTS agent_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    wallet_id UUID REFERENCES whale_wallets(id) ON DELETE SET NULL,
    wallet_movement_id UUID REFERENCES wallet_movements(id) ON DELETE SET NULL,
    alert_type TEXT NOT NULL,
    severity TEXT NOT NULL DEFAULT 'review',
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    data_quality_score INTEGER NOT NULL DEFAULT 0,
    manual_review_required BOOLEAN NOT NULL DEFAULT TRUE,
    decision_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    acknowledged_at TIMESTAMPTZ,
    CONSTRAINT agent_alerts_data_quality_score_check CHECK (data_quality_score BETWEEN 0 AND 100),
    CONSTRAINT agent_alerts_severity_check CHECK (severity IN ('info', 'review', 'urgent'))
);

CREATE INDEX IF NOT EXISTS idx_agent_alerts_review_created
    ON agent_alerts (manual_review_required, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_agent_alerts_wallet_created
    ON agent_alerts (wallet_id, created_at DESC);
