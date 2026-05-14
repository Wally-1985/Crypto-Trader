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

BACKUP_DIR=${BACKUP_DIR:-./backups}
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
DB_NAME=${POSTGRES_DB:-crypto_wallet_intelligence}
DB_USER=${POSTGRES_USER:-cwi_app}
DB_HOST=${POSTGRES_HOST:-127.0.0.1}
DB_PORT=${POSTGRES_PORT:-5432}
if [ -n "${POSTGRES_PASSWORD:-}" ] && [ -z "${PGPASSWORD:-}" ]; then
  export PGPASSWORD="$POSTGRES_PASSWORD"
fi
OUTPUT_FILE="$BACKUP_DIR/crypto-wallet-intelligence-db-$TIMESTAMP.dump"

if ! command -v pg_dump >/dev/null 2>&1; then
  echo "pg_dump is not installed. Install PostgreSQL client tools before backing up." >&2
  exit 1
fi

mkdir -p "$BACKUP_DIR"

pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -Fc -f "$OUTPUT_FILE"

sha256sum "$OUTPUT_FILE" > "$OUTPUT_FILE.sha256"

echo "Backup complete: $OUTPUT_FILE"
echo "Checksum: $OUTPUT_FILE.sha256"
