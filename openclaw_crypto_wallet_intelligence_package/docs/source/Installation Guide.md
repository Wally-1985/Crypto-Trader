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

## Ollama Setup

Install Ollama and run:

```bash
ollama pull qwen3:4b
```

## Paid Model Setup

Configure ChatGPT as the primary development model and Anthropic as fallback.

## Backup and Restore

Use the backup and restore scripts in `/backup`.

## Validation Checklist

- Backend starts
- Frontend starts
- PostgreSQL connects
- Ollama responds with qwen3:4b
- ChatGPT primary model is available
- Anthropic fallback is available
- ASVS register exists
- No secrets are committed
