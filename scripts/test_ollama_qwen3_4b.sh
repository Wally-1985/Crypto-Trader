#!/usr/bin/env bash
set -euo pipefail

if ! command -v ollama >/dev/null 2>&1; then
  echo "Ollama is not installed. Install Ollama first, then rerun this script."
  exit 1
fi

if ! curl -fsS --max-time 5 http://127.0.0.1:11434/api/tags >/tmp/ollama-tags.json; then
  echo "Ollama API is not reachable at http://127.0.0.1:11434"
  exit 1
fi

if ! ollama list | awk '{print $1}' | grep -Fxq 'qwen3:4b'; then
  echo "qwen3:4b is missing. Pull it with: ollama pull qwen3:4b"
  exit 1
fi

unexpected_models=$(ollama list | awk 'NR>1 {print $1}' | grep -Fvx 'qwen3:4b' || true)
if [ -n "$unexpected_models" ]; then
  echo "Unexpected local Ollama models found. Project policy allows qwen3:4b only:" >&2
  echo "$unexpected_models" >&2
  exit 1
fi

curl -fsS http://127.0.0.1:11434/api/generate \
  -H 'Content-Type: application/json' \
  -d '{"model":"qwen3:4b","prompt":"Reply with exactly: qwen3:4b ready","stream":false}' \
  | python3 -c 'import json,sys; print(json.load(sys.stdin).get("response", ""))'

echo "Ollama qwen3:4b validation complete."
