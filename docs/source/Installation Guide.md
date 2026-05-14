# Installation Guide

App version: v0.1.0-dev

This guide must be updated after installation, infrastructure, dependency, model, database, backup or environment changes.

## Overview

This application runs on an Ubuntu 24.04 computer with OpenClaw, PostgreSQL, Ollama qwen3:4b, FastAPI, React and background workers.

## Required Services

- OpenClaw
- PostgreSQL
- Ollama with qwen3:4b
- FastAPI backend
- React frontend
- Background workers

## Environment Variables

Use `.env.example` as the template. Do not commit the real `.env` file.

## PostgreSQL Setup

Use Docker Compose or native PostgreSQL. PostgreSQL must not be exposed to the internet.

Stage 0 Docker Compose configuration is provided in the repository root:

```bash
docker compose up -d postgres
```

The included configuration binds PostgreSQL to localhost only:

```text
127.0.0.1:5432:5432
```

Required extensions for the first migration:

- `pgcrypto`
- `uuid-ossp`

## Ollama Setup

Install Ollama and run:

```bash
ollama pull qwen3:4b
```

## Paid Model Setup

Configure ChatGPT as the primary development model and Anthropic as fallback.

Stage 0 model routing policy:

1. Ollama `qwen3:4b` for low-risk cleanup, classification, extraction, tagging and first-pass summaries.
2. ChatGPT/OpenAI as the primary paid development/reasoning provider.
3. Anthropic as fallback when ChatGPT/OpenAI token, context, rate or quota limits block progress.
4. Latest suitable paid models only for final higher-risk production/research analysis later.

Configure API keys only in the real `.env` file or host secret manager:

```text
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
```

Do not commit real API keys. Do not expose paid provider keys to frontend code.

Fallback events are recorded through the `model_task_logs` foundation. Logs must not store prompts, raw responses, API keys or secrets.

## Backup and Restore

Use the backup and restore scripts in `/backup`.

Stage 0 scripts:

- `backup/backup_postgres.sh`
- `backup/restore_postgres.sh`
- `backup/backup_app_config.sh`
- `backup/restore_app_config.sh`

Do not include unencrypted secrets in backups.

## Validation Checklist

Run structural validation:

```bash
./scripts/stage0_validate.sh
```

Stage 0 checklist:

- Backend skeleton imports and exposes `/health`
- Frontend skeleton exists and builds once Node dependencies are installed
- PostgreSQL Docker Compose config binds to localhost only
- Ollama is installed and responds with `qwen3:4b`
- ChatGPT primary model is configured through environment/provider settings
- Anthropic fallback is configured through environment/provider settings
- Mock fallback tests cover token/rate-limit fallback behaviour
- `model_task_logs` migration foundation exists for fallback event logging
- ASVS register exists and records that latest stable ASVS must be checked at audit time
- No secrets are committed
