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

MIGRATIONS_DIR=${MIGRATIONS_DIR:-database/migrations}
DB_NAME=${POSTGRES_DB:-crypto_wallet_intelligence}
DB_USER=${POSTGRES_USER:-cwi_app}
DB_HOST=${POSTGRES_HOST:-127.0.0.1}
DB_PORT=${POSTGRES_PORT:-5432}
if [ -n "${POSTGRES_PASSWORD:-}" ] && [ -z "${PGPASSWORD:-}" ]; then
  export PGPASSWORD="$POSTGRES_PASSWORD"
fi

if ! command -v psql >/dev/null 2>&1; then
  echo "psql is not installed. Install PostgreSQL client tools before applying migrations." >&2
  exit 1
fi

if [ ! -d "$MIGRATIONS_DIR" ]; then
  echo "Migrations directory not found: $MIGRATIONS_DIR" >&2
  exit 1
fi

psql_base=(psql -v ON_ERROR_STOP=1 -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME")

"${psql_base[@]}" <<'SQL'
CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
SQL

for migration in "$MIGRATIONS_DIR"/*.sql; do
  [ -e "$migration" ] || continue
  version="$(basename "$migration")"
  already_applied=$("${psql_base[@]}" -Atc "SELECT 1 FROM schema_migrations WHERE version = '$version'" || true)
  if [ "$already_applied" = "1" ]; then
    echo "Skipping already applied migration: $version"
    continue
  fi

  echo "Applying migration: $version"
  "${psql_base[@]}" <<SQL
BEGIN;
\\i $migration
INSERT INTO schema_migrations (version) VALUES ('$version');
COMMIT;
SQL
done

echo "Database migrations complete."
