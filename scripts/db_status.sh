#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  . ./.env
  set +a
fi

DB_NAME=${POSTGRES_DB:-crypto_wallet_intelligence}
DB_USER=${POSTGRES_USER:-cwi_app}
DB_HOST=${POSTGRES_HOST:-127.0.0.1}
DB_PORT=${POSTGRES_PORT:-5432}
if [ -n "${POSTGRES_PASSWORD:-}" ] && [ -z "${PGPASSWORD:-}" ]; then
  export PGPASSWORD="$POSTGRES_PASSWORD"
fi

if ! command -v psql >/dev/null 2>&1; then
  echo "psql is not installed. PostgreSQL runtime validation is blocked."
  exit 1
fi

psql -v ON_ERROR_STOP=1 -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" <<'SQL'
SELECT current_database() AS database, current_user AS app_user, inet_server_addr() AS server_addr, inet_server_port() AS server_port;
SELECT extname FROM pg_extension WHERE extname IN ('pgcrypto', 'uuid-ossp') ORDER BY extname;
SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name IN (
    'schema_migrations',
    'model_task_logs',
    'whale_wallets',
    'watchlist',
    'wallet_movements',
    'agent_alerts',
    'signal_outcomes',
    'token_mappings'
) ORDER BY table_name;
SQL
