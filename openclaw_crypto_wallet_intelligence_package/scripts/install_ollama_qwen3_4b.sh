#!/usr/bin/env bash
set -euo pipefail

if ! command -v ollama >/dev/null 2>&1; then
  echo "Ollama is not installed. Install Ollama first, then rerun this script."
  exit 1
fi

ollama pull qwen3:4b
ollama list | grep -i "qwen3" || true
