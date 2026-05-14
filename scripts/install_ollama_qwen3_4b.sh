#!/usr/bin/env bash
set -euo pipefail

# Project policy: local Ollama only, with qwen3:4b as the only approved local model.
export OLLAMA_HOST="${OLLAMA_HOST:-127.0.0.1:11434}"

if ! command -v ollama >/dev/null 2>&1; then
  echo "Ollama is not installed or is not on PATH." >&2
  echo "Install Ollama from https://ollama.com/download, or add ~/.local/bin to PATH if using a user-space install." >&2
  exit 1
fi

if ! curl -fsS --max-time 5 "http://${OLLAMA_HOST}/api/tags" >/dev/null; then
  echo "Ollama API is not reachable at http://${OLLAMA_HOST}." >&2
  echo "Start Ollama locally with: OLLAMA_HOST=${OLLAMA_HOST} ollama serve" >&2
  exit 1
fi

ollama pull qwen3:4b

unexpected_models=$(ollama list | awk 'NR>1 {print $1}' | grep -Fvx 'qwen3:4b' || true)
if [ -n "$unexpected_models" ]; then
  echo "Unexpected local Ollama models found. Project policy allows qwen3:4b only:" >&2
  echo "$unexpected_models" >&2
  exit 1
fi

ollama list | awk '{print $1}' | grep -Fxq 'qwen3:4b'
echo "Ollama qwen3:4b is installed and policy-compliant."
