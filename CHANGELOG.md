# Changelog

## v0.1.0-dev

- Initial starter package created.
- Added staged development plan.
- Added OpenClaw prompt package.
- Added project memory files.
- Added agent role files.
- Added ASVS audit templates.
- Added backup and restore script templates.
- Added First Installation guide.
- Normalized repository structure so project directories live at the Git repo root.
- Added Stage 0 FastAPI backend skeleton with configuration, health route and model routing policy foundation.
- Added Stage 0 React + Vite frontend skeleton.
- Added database migration/seed placeholders and worker foundation notes.
- Added Stage 0 ASVS control register foundation.
- Added Stage 0 structural validation script.
- Implemented Anthropic fallback routing foundation for paid development tasks when ChatGPT/OpenAI hits token, context, rate or quota limits.
- Added mock tests for fallback behaviour.
- Added `model_task_logs` migration foundation for safe model routing/fallback event logging.
- Added local Ollama `qwen3:4b` health/client foundation and validation scripts.
- Validated a local user-space Ollama install bound to `127.0.0.1:11434` with only `qwen3:4b` present.
- Added PostgreSQL migration/status scripts, stricter localhost validation and backup/restore tool checks.
- Validated Docker Compose PostgreSQL runtime, Stage 0 migrations and PostgreSQL backup creation on the host.
- Added persistent user-space systemd service for local-only Ollama `qwen3:4b` runtime.
- Started Stage 1 with whale wallet, watchlist, wallet movement and agent alert database foundations plus initial wallet management API routes.
- Added Whale Wallets frontend screen wired to `/wallets`, with wallet creation, chain filtering, summary cards and enable/disable controls.
