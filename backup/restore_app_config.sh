#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 path/to/config-backup.tar.gz"
  exit 1
fi

tar -xzf "$1"
echo "Config restore complete. Review files before starting services."
