# ASVS Control Register — Stage 0 Foundation

Application version: v0.1.0-dev
ASVS version used: To be confirmed against the latest stable OWASP ASVS version at audit time.
Target score: At least 90% across applicable controls.

## Stage 0 Register Notes

This is the foundation register. It records security posture before feature development. Do not mark controls as passed without evidence.

| Area | Stage 0 expectation | Status | Evidence |
| --- | --- | --- | --- |
| Secrets management | Real `.env`, API keys, wallet private keys, seed phrases and withdrawal keys are not committed. | Foundation created | `.gitignore`, `.env.example`, Stage 0 validation script, config backup excludes `.env` |
| Database exposure | PostgreSQL is bound to localhost only when using Docker Compose. | Validated on host | `docker-compose.yml`, `.env.example`, `scripts/stage0_validate.sh`, `docker compose ps` showing `127.0.0.1:5432->5432/tcp` |
| Local model exposure | Ollama must remain local-only and use `qwen3:4b` only. | Validated on host | `.env.example`, `scripts/install_ollama_qwen3_4b.sh`, `scripts/test_ollama_qwen3_4b.sh`, user service `~/.config/systemd/user/ollama.service`, local API check at `127.0.0.1:11434` |
| Model output safety | Model output must not directly execute shell commands, trades or security changes. | Foundation created | `memory/Agent Operating Rules.md`, backend routing comments |
| Model provider fallback logging | Fallback from ChatGPT/OpenAI to Anthropic and local Ollama model-task routing must be logged without storing prompts, raw responses, API keys or secrets. | Foundation created | `backend/app/core/model_routing.py`, `backend/app/core/model_task_logs.py`, `backend/app/core/ollama_client.py`, `database/migrations/0001_stage0_model_task_logs.sql` |
| Trading safety | V1 live trading is disabled. | Foundation created | `.env.example`, backend settings/tests |
| Wallet data safety | Wallet tracking stores public wallet intelligence only; no private keys, seed phrases or withdrawal keys. | Foundation created | `database/migrations/0002_stage1_wallet_tracking.sql`, wallet API schemas |
| Audit process | Latest stable ASVS version must be checked at audit time. | Foundation created | `security/asvs/ASVS Audit v0.1.0-dev.md`, docs source |
