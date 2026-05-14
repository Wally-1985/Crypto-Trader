#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

./scripts/stage1_validate.sh

required_paths=(
  database/migrations/0004_stage2_signal_outcomes.sql
  backend/app/api/outcomes.py
  backend/app/services/signal_outcomes.py
  backend/app/services/market_data.py
  backend/tests/test_stage2.py
)

for path in "${required_paths[@]}"; do
  if [ ! -e "$path" ]; then
    echo "missing Stage 2 path: $path" >&2
    exit 1
  fi
done

if ! grep -q 'CREATE TABLE IF NOT EXISTS signal_outcomes' database/migrations/0004_stage2_signal_outcomes.sql; then
  echo "Stage 2 migration missing signal_outcomes table" >&2
  exit 1
fi

for horizon in 15m 1h 4h 24h 7d; do
  if ! grep -q "'$horizon'" database/migrations/0004_stage2_signal_outcomes.sql; then
    echo "Stage 2 migration missing horizon: $horizon" >&2
    exit 1
  fi
done

if ! grep -q 'coingecko_public' backend/app/api/outcomes.py; then
  echo "Stage 2 outcomes API must expose the read-only public market-data provider option" >&2
  exit 1
fi

if ! grep -q 'paper_trading_only = TRUE' database/migrations/0004_stage2_signal_outcomes.sql; then
  echo "Stage 2 outcomes must enforce paper_trading_only" >&2
  exit 1
fi

python3 -m compileall -q backend/app backend/tests

if [ -x .venv/bin/pytest ]; then
  .venv/bin/pytest backend/tests -q
else
  echo "WARN: .venv pytest is unavailable; skipping pytest validation."
fi

npm --prefix frontend run build

if command -v psql >/dev/null 2>&1 && [ -f .env ]; then
  ./scripts/db_status.sh >/tmp/stage2_db_status.txt
  if ! grep -q "signal_outcomes" /tmp/stage2_db_status.txt; then
    echo "Database status missing Stage 2 table: signal_outcomes" >&2
    cat /tmp/stage2_db_status.txt >&2
    exit 1
  fi
else
  echo "WARN: psql or .env unavailable; skipping Stage 2 runtime table validation."
fi

echo "Stage 2 validation passed."
