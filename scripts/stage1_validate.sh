#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

./scripts/stage0_validate.sh

required_paths=(
  database/migrations/0002_stage1_wallet_tracking.sql
  backend/app/api/wallets.py
  backend/app/api/movements.py
  backend/app/api/alerts.py
  backend/app/api/polling.py
  backend/app/core/wallet_policy.py
  backend/app/workers/wallet_polling.py
  backend/app/schemas/wallets.py
  backend/tests/test_stage1.py
)

for path in "${required_paths[@]}"; do
  if [ ! -e "$path" ]; then
    echo "missing Stage 1 path: $path" >&2
    exit 1
  fi
done

for table in whale_wallets watchlist wallet_movements agent_alerts; do
  if ! grep -q "CREATE TABLE IF NOT EXISTS $table" database/migrations/0002_stage1_wallet_tracking.sql; then
    echo "Stage 1 migration missing table: $table" >&2
    exit 1
  fi
done

if ! grep -q 'manual_review_required' database/migrations/0002_stage1_wallet_tracking.sql; then
  echo "Stage 1 migration must include manual_review_required fields" >&2
  exit 1
fi

if ! grep -q 'data_quality_score' database/migrations/0002_stage1_wallet_tracking.sql; then
  echo "Stage 1 migration must include data_quality_score fields" >&2
  exit 1
fi

if ! grep -q 'UNIQUE (chain, normalized_address)' database/migrations/0002_stage1_wallet_tracking.sql; then
  echo "Stage 1 wallet table must prevent duplicate chain/address records" >&2
  exit 1
fi

python3 -m compileall -q backend/app backend/tests

if [ -x .venv/bin/pytest ]; then
  .venv/bin/pytest backend/tests -q
else
  echo "WARN: .venv pytest is unavailable; skipping pytest validation."
fi

if command -v psql >/dev/null 2>&1 && [ -f .env ]; then
  ./scripts/db_status.sh >/tmp/stage1_db_status.txt
  for table in whale_wallets watchlist wallet_movements agent_alerts; do
    if ! grep -q "$table" /tmp/stage1_db_status.txt; then
      echo "Database status missing Stage 1 table: $table" >&2
      cat /tmp/stage1_db_status.txt >&2
      exit 1
    fi
  done
else
  echo "WARN: psql or .env unavailable; skipping Stage 1 runtime table validation."
fi

echo "Stage 1 validation passed."
