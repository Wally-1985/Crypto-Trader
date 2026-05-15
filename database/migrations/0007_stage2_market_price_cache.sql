-- Stage 2 read-only market price cache for public market-data rate-limit protection.
-- Stores public provider responses only; no secrets, orders, private keys or trading credentials.

CREATE TABLE IF NOT EXISTS market_price_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider TEXT NOT NULL,
    provider_token_id TEXT NOT NULL,
    vs_currency TEXT NOT NULL DEFAULT 'usd',
    price_usd NUMERIC(30, 12),
    observed_at TIMESTAMPTZ NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    source TEXT NOT NULL,
    raw_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT market_price_cache_unique_token UNIQUE (provider, provider_token_id, vs_currency)
);

CREATE INDEX IF NOT EXISTS idx_market_price_cache_lookup
    ON market_price_cache (provider, provider_token_id, vs_currency, expires_at DESC);

INSERT INTO market_price_cache (
    provider, provider_token_id, vs_currency, price_usd, observed_at, expires_at, source, raw_payload
)
SELECT DISTINCT ON (raw_api_payload->>'enrichment_provider', raw_api_payload->>'provider_token_id')
    raw_api_payload->>'enrichment_provider' AS provider,
    raw_api_payload->>'provider_token_id' AS provider_token_id,
    'usd' AS vs_currency,
    price_at_trade_time AS price_usd,
    COALESCE((raw_api_payload->>'price_observed_at')::timestamptz, updated_at) AS observed_at,
    now() + interval '10 minutes' AS expires_at,
    COALESCE(raw_api_payload->>'price_source', 'movement_enrichment_backfill') AS source,
    jsonb_build_object(
        'source', 'movement_enrichment_backfill',
        'movement_id', id,
        'paper_trading_only', TRUE
    ) AS raw_payload
FROM wallet_movements
WHERE price_at_trade_time IS NOT NULL
  AND raw_api_payload->>'enrichment_provider' IS NOT NULL
  AND raw_api_payload->>'provider_token_id' IS NOT NULL
ORDER BY raw_api_payload->>'enrichment_provider', raw_api_payload->>'provider_token_id', updated_at DESC
ON CONFLICT (provider, provider_token_id, vs_currency)
DO UPDATE SET
    price_usd = EXCLUDED.price_usd,
    observed_at = EXCLUDED.observed_at,
    expires_at = EXCLUDED.expires_at,
    source = EXCLUDED.source,
    raw_payload = EXCLUDED.raw_payload,
    updated_at = now();
