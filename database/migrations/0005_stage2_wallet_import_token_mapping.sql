-- Stage 2 wallet intake and token identity mapping.
-- Read-only research/paper-trading foundation. No private keys, seed phrases, exchange keys or trading credentials.

CREATE TABLE IF NOT EXISTS token_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chain TEXT NOT NULL,
    token_symbol TEXT NOT NULL,
    token_contract TEXT,
    provider TEXT NOT NULL DEFAULT 'coingecko_public',
    provider_token_id TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'manual',
    confidence_score INTEGER NOT NULL DEFAULT 80,
    notes TEXT,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT token_mappings_confidence_check CHECK (confidence_score BETWEEN 0 AND 100)
);

CREATE UNIQUE INDEX IF NOT EXISTS token_mappings_unique_provider_symbol_contract
    ON token_mappings (chain, token_symbol, COALESCE(token_contract, ''), provider);

CREATE INDEX IF NOT EXISTS idx_token_mappings_lookup
    ON token_mappings (enabled, provider, chain, token_symbol);

CREATE INDEX IF NOT EXISTS idx_token_mappings_contract
    ON token_mappings (chain, token_contract)
    WHERE token_contract IS NOT NULL;
