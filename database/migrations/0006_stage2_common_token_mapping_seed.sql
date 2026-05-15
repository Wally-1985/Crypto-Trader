-- Stage 2 common token mapping seed for wallet-led movement enrichment.
-- Provider IDs are public CoinGecko IDs. No secrets or trading credentials.

INSERT INTO token_mappings (chain, token_symbol, token_contract, provider, provider_token_id, source, confidence_score, notes, enabled)
VALUES
  ('ethereum', 'ETH', NULL, 'coingecko_public', 'ethereum', 'seed_common_tokens', 95, 'Native ETH CoinGecko mapping.', TRUE),
  ('ethereum', 'USDC', '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48', 'coingecko_public', 'usd-coin', 'seed_common_tokens', 95, 'Ethereum USDC contract mapping.', TRUE),
  ('ethereum', 'USDC', NULL, 'coingecko_public', 'usd-coin', 'seed_common_tokens', 90, 'Generic USDC mapping.', TRUE),
  ('ethereum', 'AETHUSDC', '0x98c23e9d8f34fefb1b7bd6a91b7ff122f4e16f5c', 'coingecko_public', 'usd-coin', 'seed_common_tokens', 70, 'Aave aEthUSDC receipt token; priced as USDC proxy for review-only enrichment.', TRUE)
ON CONFLICT (chain, token_symbol, COALESCE(token_contract, ''), provider)
DO UPDATE SET
  provider_token_id = EXCLUDED.provider_token_id,
  source = EXCLUDED.source,
  confidence_score = EXCLUDED.confidence_score,
  notes = EXCLUDED.notes,
  enabled = EXCLUDED.enabled,
  updated_at = now();
