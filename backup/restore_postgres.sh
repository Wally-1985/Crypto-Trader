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

if [ $# -lt 1 ]; then
  echo "Usage: $0 path/to/backup.dump"
  exit 1
fi

BACKUP_FILE="$1"
DB_NAME=${POSTGRES_DB:-crypto_wallet_intelligence}
DB_USER=${POSTGRES_USER:-cwi_app}
DB_HOST=${POSTGRES_HOST:-127.0.0.1}
DB_PORT=${POSTGRES_PORT:-5432}
if [ -n "${POSTGRES_PASSWORD:-}" ] && [ -z "${PGPASSWORD:-}" ]; then
  export PGPASSWORD="$POSTGRES_PASSWORD"
fi

if ! command -v pg_restore >/dev/null 2>&1; then
  echo "pg_restore is not installed. Install PostgreSQL client tools before restoring." >&2
  exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
  echo "Backup file not found: $BACKUP_FILE"
  exit 1
fi

if [ -f "$BACKUP_FILE.sha256" ]; then
  sha256sum -c "$BACKUP_FILE.sha256"
fi

pg_restore -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" --clean --if-exists "$BACKUP_FILE"

echo "Restore complete: $BACKUP_FILE"
