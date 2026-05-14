#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR=${BACKUP_DIR:-./backups}
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
OUTPUT_FILE="$BACKUP_DIR/crypto-wallet-intelligence-config-$TIMESTAMP.tar.gz"

mkdir -p "$BACKUP_DIR"

tar --exclude='.env' --exclude='*.dump' --exclude='backups' -czf "$OUTPUT_FILE" \
  .env.example README.md CHANGELOG.md DEVELOPMENT_PLAN.md docs security backup scripts docker-compose.yml

sha256sum "$OUTPUT_FILE" > "$OUTPUT_FILE.sha256"

echo "Config backup complete: $OUTPUT_FILE"
