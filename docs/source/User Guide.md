# User Guide

App version: v0.1.0-dev

This guide must be updated after user-facing workflow or screen changes.

## Overview

The Crypto Wallet Intelligence and Paper Trading App monitors watched wallets, detects patterns, researches wallet-triggered coin activity, creates scored paper-trade candidates and reports whether signals worked.

## Key Pages

- Dashboard
- Settings
- Whale Wallets
- Wallet Movements
- Whale Trend Clusters
- Wallet Relationships
- Pattern Alerts
- Research Notes
- Copy Trade Candidates
- Paper Trading
- Reports
- Agent Logs
- Model Task Logs

## Important Concepts

- Data Quality Score
- Liquidity Score
- Source Reliability Score
- Too-Late Score
- Wallet Influence Score
- Decision Snapshot
- Manual Review Required
- Emergency Stop

## Safety Limits

V1 is paper trading only. It cannot execute live trades.

## Whale Wallets Page

The Whale Wallets screen is the first Stage 1 user-facing workflow. It connects to the backend `/wallets` and `/wallet-movements` APIs.

Current wallet actions:

- View wallet summary counts.
- List watched wallets.
- Filter listed wallets by chain.
- Add a watched wallet.
- Classify wallet type.
- Set alert threshold, watch priority and confidence weighting.
- Add tags and sectors of interest.
- Mark a wallet as paper copy-review allowed.
- Mark a wallet as Do Not Copy.
- Enable or disable an existing wallet.

Current movement actions:

- Manually store a wallet movement for smoke testing and research history.
- Record movement type, transaction hash, token, estimated USD value, protocol, transaction time and data quality score.
- View recent movements.
- Filter movements by manual-review requirement or large-alert status.
- Automatically create a review alert when a stored movement crosses the watched wallet's configured USD threshold.

Current alert and polling actions:

- Review generated agent alerts.
- Inspect decision snapshots for paper-trading-only context.
- Acknowledge reviewed alerts.
- Run a dry-run polling skeleton that checks enabled, non-Do-Not-Copy wallets without using external provider keys.
- Run deterministic mock ingestion to validate the full provider pipeline without real chain APIs.
- Review data quality score reasons on movement decision snapshots.
- Track alert status, candidate decision and analyst notes through the backend API.

Available backend routes:

- `GET /wallets` — list watched wallets.
- `POST /wallets` — add a watched wallet.
- `GET /wallets/{wallet_id}` — get one watched wallet.
- `PATCH /wallets/{wallet_id}` — update wallet metadata and policy fields.
- `PATCH /wallets/{wallet_id}/enabled` — enable or disable a watched wallet.
- `GET /wallets/summary` — wallet and movement counts.
- `GET /wallet-movements` — list/filter wallet movements.
- `POST /wallet-movements` — manually store a wallet movement and create review alerts when thresholds are crossed.
- `GET /agent-alerts` — list/filter generated alerts.
- `PATCH /agent-alerts/{alert_id}/acknowledge` — acknowledge an alert after review.
- `POST /wallet-polling/run-once?provider=dry_run` — run the Stage 1 dry-run polling skeleton.
- `POST /wallet-polling/run-once?provider=mock` — run deterministic mock provider ingestion through validate, score, dedupe, store and alert.

Wallet records support enabled/disabled status, wallet type, tags, sectors, alert threshold, watch priority, confidence weighting, copy-trade disabled/enabled flag, and Do Not Copy policy. Movement records support data quality score, data quality reasons and manual-review flags. Alerts preserve decision snapshots and support review status, analyst notes and candidate decisions. V1 remains paper-trading only.
