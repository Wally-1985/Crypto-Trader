# First Installation

## Purpose

This package is the starting point for building the Crypto Wallet Intelligence and Paper Trading App in OpenClaw.

You have a clean Ubuntu 24.04 computer with OpenClaw installed and ChatGPT connected. Nothing else is assumed to be installed.

The first objective is to get the project into GitHub, configure OpenClaw with the project memory and prompts, install PostgreSQL, install Ollama with `qwen3:4b`, and add Anthropic as the fallback paid model.

## What This Package Contains

- `DEVELOPMENT_PLAN.md` - the staged development plan OpenClaw should manage.
- `memory/` - project memory files to give OpenClaw long-term context.
- `agents/` - agent role files for compartmentalised development.
- `docs/openclaw-prompts/` - prompts for kickoff, reinstall, setup and maintenance.
- `docs/source/` - source documents for guides and audit files.
- `docs/pdf/` - generated PDF documents.
- `security/asvs/` - ASVS audit templates and control register.
- `backup/` - backup and restore scripts.
- `.env.example` - environment variable template.
- `docker-compose.yml` - initial PostgreSQL Docker Compose file.

## First Steps

### 1. Extract the package

Copy the zip file to your Ubuntu computer and extract it:

```bash
unzip openclaw_crypto_wallet_intelligence_starter.zip
cd openclaw_crypto_wallet_intelligence_package
```

### 2. Create a GitHub repository

Create a new private GitHub repository, then push this starter package into it.

Example:

```bash
git init
git add .
git commit -m "Initial OpenClaw crypto wallet intelligence starter package"
git branch -M main
git remote add origin YOUR_GITHUB_REPOSITORY_URL
git push -u origin main
```

Do not commit real secrets or real `.env` files.

### 3. Give OpenClaw the project memory

In OpenClaw, add the files from `/memory` as project memory/context:

- `Project Memory.md`
- `Agent Operating Rules.md`
- `Security Memory.md`
- `Product Vision.md`

These files tell OpenClaw what the system is, how it should behave, what must not be built, and how to prioritise work.

### 4. Give OpenClaw the initial kickoff prompt

Open:

`docs/openclaw-prompts/00_Initial_Kickoff_Prompt.md`

Paste it into OpenClaw and instruct it to begin Stage 0 only.

Do not ask OpenClaw to build the entire system in one pass.

### 5. Add Anthropic fallback early

Open:

`docs/openclaw-prompts/03_Anthropic_Fallback_Setup_Prompt.md`

Use this prompt after the project repo exists and before heavy development begins.

Development routing should be:

1. Ollama qwen3:4b for low-risk cleanup and classification.
2. ChatGPT as the primary development model.
3. Anthropic as fallback if ChatGPT token limits are reached.
4. Latest suitable paid models only when the final system is used for higher-risk analysis.

### 6. Install Ollama and qwen3:4b early

Open:

`docs/openclaw-prompts/02_Ollama_Setup_Prompt.md`

The only local model to install is:

```bash
ollama pull qwen3:4b
```

OpenClaw should confirm the model responds before continuing with research or scraping features.

### 7. Install PostgreSQL

Open:

`docs/openclaw-prompts/04_PostgreSQL_Setup_Prompt.md`

OpenClaw should help configure PostgreSQL locally using either Docker Compose or a native install. The included Docker Compose file binds PostgreSQL to localhost only.

### 8. Follow the staged plan

OpenClaw must work stage by stage:

1. Stage 0 - Foundation, repository, security and local infrastructure
2. Stage 1 - Wallet database and movement tracking
3. Stage 2 - Price outcomes and signal validation
4. Stage 3 - Core pattern intelligence
5. Stage 4 - Controlled research
6. Stage 5 - Copy-trade candidates and paper trading
7. Stage 6 - Reporting and feedback optimisation

V1 is not complete until Stage 6 is complete and ASVS score is at least 90%.

## Important Safety Rules

V1 must not execute real trades.

The system must not:

- Store wallet private keys
- Ask for seed phrases
- Store exchange withdrawal keys
- Use margin
- Use leverage
- Use futures
- Execute live trades
- Expose PostgreSQL to the internet
- Expose Ollama to the internet
- Commit secrets to GitHub

## Documentation Rules

The following PDFs must exist and be updated after relevant changes:

- `First Installation.pdf`
- `Installation Guide.pdf`
- `User Guide.pdf`
- `ASVS Audit (App version number).pdf`

The ASVS audit filename uses the app version number. The audit document must record the latest stable OWASP ASVS version used.

## Backup and Migration

Backup and restore must be implemented early.

The goal is to make it easy to move this system later to a more powerful computer by:

1. Cloning the GitHub repository.
2. Installing dependencies.
3. Pulling Ollama qwen3:4b.
4. Restoring the PostgreSQL backup.
5. Configuring `.env`.
6. Running migrations.
7. Starting backend, frontend and workers.
8. Running validation checks.

Use the prompts and scripts in this package to maintain that migration path from the beginning.

## Recommended First OpenClaw Instruction

Paste this into OpenClaw after loading the memory files:

```text
Use the repository files and project memory provided. Begin Stage 0 only. Do not build application features yet. Create the repository structure, configure documentation, set up PostgreSQL, install and test Ollama qwen3:4b, add Anthropic fallback model routing, create the initial FastAPI and React skeletons, create the ASVS audit register foundation, and update the README. Stop after Stage 0 validation and provide a summary of what was completed and what still needs manual configuration.
```
