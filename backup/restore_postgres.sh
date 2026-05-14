#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 path/to/backup.dump"
  exit 1
fi

BACKUP_FILE="$1"
DB_NAME=${POSTGRES_DB:-crypto_wallet_intelligence}
DB_USER=${POSTGRES_USER:-cwi_app}
DB_HOST=${POSTGRES_HOST:-localhost}
DB_PORT=${POSTGRES_PORT:-5432}

if [ ! -f "$BACKUP_FILE" ]; then
  echo "Backup file not found: $BACKUP_FILE"
  exit 1
fi

pg_restore -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" --clean --if-exists "$BACKUP_FILE"

echo "Restore complete: $BACKUP_FILE"
