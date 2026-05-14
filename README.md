# Crypto Wallet Intelligence and Paper Trading App - OpenClaw Starter Package

This repository contains the starting application skeleton, documentation, prompts, memory files, agent role files, security templates, backup/restore scripts and development plan needed to build the project in OpenClaw.

## Start Here

1. Read `docs/pdf/First Installation.pdf`.
2. Read `DEVELOPMENT_PLAN.md`.
3. Import or paste the memory files from `/memory` into OpenClaw as project memory/context.
4. Give OpenClaw the prompt in `docs/openclaw-prompts/00_Initial_Kickoff_Prompt.md`.
5. Prioritise Stage 0 work first: GitHub repo, FastAPI skeleton, React + Vite skeleton, PostgreSQL, Ollama `qwen3:4b`, Anthropic fallback, documentation and ASVS baseline.

## Key Requirements

- Ubuntu 24.04 host with OpenClaw already installed.
- Ollama must be installed early and use only `qwen3:4b`.
- ChatGPT is the primary development model.
- Anthropic must be added quickly as the fallback model if ChatGPT token limits are reached.
- During development, use cost-effective non-latest paid models where suitable.
- When the finished system moves into actual use, configure it to use the latest suitable paid models for higher-risk reasoning and final analysis.
- PostgreSQL must be self-hosted on the same computer at first.
- The app must be developed against the latest stable OWASP ASVS version at the time of development or audit, and score at least 90% across applicable controls.
- V1 is research and paper-trading only. No live trading.

## Included Files

- `DEVELOPMENT_PLAN.md` - staged development plan for OpenClaw.
- `docs/pdf/First Installation.pdf` - how to use this package and start development.
- `docs/source/First Installation.md` - source for the PDF.
- `docs/source/Installation Guide.md` - installation guide source template.
- `docs/source/User Guide.md` - user guide source template.
- `docs/source/ASVS Audit Template.md` - ASVS audit source template.
- `docs/openclaw-prompts/` - prompts to drive OpenClaw.
- `memory/` - project memory and operating rules.
- `agents/` - agent role/personality files.
- `security/asvs/` - ASVS register and evidence templates.
- `backup/` - PostgreSQL and config backup/restore scripts.
- `backend/` - Stage 0 FastAPI skeleton, configuration and model routing policy.
- `frontend/` - Stage 0 React + Vite skeleton.
- `workers/` - Stage 0 worker foundation notes.
- `database/` - migration and seed foundations.
- `.env.example` - environment variable template.
- `docker-compose.yml` - initial local PostgreSQL compose file bound to `127.0.0.1` only.
- `scripts/stage0_validate.sh` - Stage 0 structural validation script.
- `scripts/db_migrate.sh` - Apply SQL migrations and track them in `schema_migrations`.
- `scripts/db_status.sh` - Validate PostgreSQL connection, required extensions and Stage 0 tables.
- `scripts/install_ollama_qwen3_4b.sh` - Pull and policy-check the approved local Ollama model.
- `scripts/test_ollama_qwen3_4b.sh` - Verify local-only Ollama API access and a `qwen3:4b` response.

## Versioning

Initial app version: `v0.1.0-dev`

ASVS audit PDFs should use the application version in the filename, for example:

`ASVS Audit v0.1.0-dev.pdf`

The ASVS version used must be recorded inside the audit document.

## Stage 0 Status

Stage 0 foundation has been normalized to the repository root and now includes:

- FastAPI backend skeleton with `/health` route.
- React + Vite frontend skeleton.
- Model routing policy foundation: Ollama `qwen3:4b` for low-risk local tasks, ChatGPT primary paid development model, Anthropic fallback on token/context/rate/quota limit errors.
- Local Ollama health/check client foundation for confirming the `qwen3:4b` API is reachable without storing prompts, raw responses, API keys or secrets.
- PostgreSQL Docker Compose foundation bound to localhost only, with migration/status scripts for Stage 0 database setup.
- ASVS register foundation with latest-stable-ASVS-at-audit-time requirement.
- `schema_migrations` runner foundation and `model_task_logs` migration foundation for safe provider/fallback event logging without storing prompts, raw responses, API keys or secrets.
- Backup/restore script foundations.

Runtime validation on this host:

- Docker and Docker Compose are installed and accessible to the OpenClaw user.
- PostgreSQL runs through Docker Compose and is bound to `127.0.0.1:5432` only.
- Stage 0 migrations have been applied and `db_status.sh` confirms `schema_migrations`, `model_task_logs`, `pgcrypto` and `uuid-ossp`.
- Ollama has been validated in a persistent user-space systemd service on this host, bound to `127.0.0.1:11434`, with only `qwen3:4b` present.

## Stage 1 Status

Stage 1 has started with the whale wallet database and movement tracking foundation:

- `whale_wallets`, `watchlist`, `wallet_movements` and `agent_alerts` migrations.
- Data quality score and manual review fields on movement/alert foundations.
- Wallet duplicate prevention by `(chain, normalized_address)`.
- Wallet policy helpers for address normalisation, wallet type validation and manual-review rules.
- Initial wallet management API routes under `/wallets`.
- Wallet movement API routes under `/wallet-movements` for manual/test movement entry and movement listing/filtering.
- Automatic review alert creation when a stored movement crosses the watched wallet's configured USD alert threshold.
- Whale Wallets frontend screen wired to `/wallets`, including add wallet, summary cards, chain filter and enable/disable controls.
- Wallet Movements frontend section for manual smoke entries, recent movement review, manual-review filtering and large-alert filtering.
