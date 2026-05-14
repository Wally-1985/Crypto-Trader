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

## Versioning

Initial app version: `v0.1.0-dev`

ASVS audit PDFs should use the application version in the filename, for example:

`ASVS Audit v0.1.0-dev.pdf`

The ASVS version used must be recorded inside the audit document.

## Stage 0 Status

Stage 0 foundation has been normalized to the repository root and now includes:

- FastAPI backend skeleton with `/health` route.
- React + Vite frontend skeleton.
- Model routing policy foundation: Ollama `qwen3:4b` for low-risk local tasks, ChatGPT primary paid development model, Anthropic fallback.
- PostgreSQL Docker Compose foundation bound to localhost only.
- ASVS register foundation with latest-stable-ASVS-at-audit-time requirement.
- Backup/restore script foundations.

Runtime blockers on this host at Stage 0 validation time:

- Docker is not currently available, so PostgreSQL container startup cannot be validated yet.
- Ollama is not currently installed, so `qwen3:4b` pull/response testing requires system installation approval first.
