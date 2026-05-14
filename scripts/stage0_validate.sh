#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

required_paths=(
  DEVELOPMENT_PLAN.md README.md CHANGELOG.md .env.example docker-compose.yml
  backend/pyproject.toml backend/app/main.py backend/app/core/config.py backend/app/core/model_routing.py backend/tests/test_stage0.py
  frontend/package.json frontend/index.html frontend/src/main.tsx frontend/vite.config.ts
  database/migrations/README.md database/seed/README.md workers/README.md
  security/asvs/ASVS\ Audit\ v0.1.0-dev.md security/asvs/ASVS\ Control\ Register\ Template.csv security/asvs/ASVS\ Evidence\ Register.md
  docs/source/First\ Installation.md docs/source/Installation\ Guide.md docs/source/User\ Guide.md docs/source/ASVS\ Audit\ Template.md
  backup/backup_postgres.sh backup/restore_postgres.sh backup/backup_app_config.sh backup/restore_app_config.sh
)

for path in "${required_paths[@]}"; do
  if [ ! -e "$path" ]; then
    echo "missing required path: $path" >&2
    exit 1
  fi
done

if grep -RInE '(private key|seed phrase|withdrawal key)' --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=dist --exclude-dir=.venv --exclude='*.pdf' . | grep -ivE 'do not|no wallet|no seed|no withdrawal|must not|never|private keys|seed phrases|withdrawal keys' >/tmp/stage0_secret_terms.txt; then
  echo "potential unsafe secret-related content found:" >&2
  cat /tmp/stage0_secret_terms.txt >&2
  exit 1
fi

if ! grep -q '127.0.0.1:5432:5432' docker-compose.yml; then
  echo "PostgreSQL must bind to 127.0.0.1 only in docker-compose.yml" >&2
  exit 1
fi

if ! grep -q 'OLLAMA_MODEL=qwen3:4b' .env.example; then
  echo "OLLAMA_MODEL must be qwen3:4b in .env.example" >&2
  exit 1
fi

if ! grep -q 'LIVE_TRADING_ENABLED=false' .env.example; then
  echo "LIVE_TRADING_ENABLED must default false" >&2
  exit 1
fi

python3 -m compileall -q backend/app

if command -v ollama >/dev/null 2>&1; then
  ollama list | grep -q 'qwen3:4b' || {
    echo "Ollama is installed but qwen3:4b is not present" >&2
    exit 1
  }
else
  echo "WARN: Ollama is not installed on this host; install/test is blocked until system install is approved."
fi

if command -v docker >/dev/null 2>&1; then
  docker compose config >/dev/null
else
  echo "WARN: Docker is not installed/available; PostgreSQL compose runtime validation is blocked."
fi

echo "Stage 0 structural validation passed."
