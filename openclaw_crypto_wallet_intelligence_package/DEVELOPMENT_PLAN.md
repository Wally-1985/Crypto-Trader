# Crypto Wallet Intelligence and Paper Trading App - Staged Development Plan

App version: `v0.1.0-dev`

## Project Objective

Build a self-hosted crypto research, whale wallet intelligence, pattern detection and paper-trading web application that runs locally on the same Ubuntu 24.04 computer as OpenClaw.

The system must identify which wallets and wallet groups are worth watching by tracking wallet movements, measuring post-trade outcomes, detecting repeatable patterns, generating scored copy-trade candidates and testing those candidates through paper trading only.

V1 must not execute live trades.

## Core Design Principles

- Wallet-led intelligence first. Broad market search is disabled by default.
- PostgreSQL is the primary database from the start.
- Ollama must be installed early and use only `qwen3:4b`.
- Use qwen3:4b for low-risk cleanup, extraction, tagging and first-pass summaries.
- Use ChatGPT for complex development and reasoning tasks.
- Add Anthropic early as fallback if ChatGPT token limits are reached.
- Use cost-effective, slightly off-current paid models during development where suitable.
- Use the latest suitable paid models when the finished system is used for high-risk research and final analysis.
- Develop against the latest stable OWASP ASVS version at the time of development or audit.
- Maintain a minimum ASVS score of 90% across applicable controls.
- Maintain Installation Guide.pdf, User Guide.pdf and ASVS Audit (App version number).pdf.
- Maintain backup and restore scripts from the beginning.
- Keep all code and documentation in GitHub.

---

# Stage 0 - Foundation, Repository, Security and Local Infrastructure

## Goal

Create the project repository, local services, documentation structure, security baseline, PostgreSQL database, Ollama qwen3:4b and paid-model fallback routing.

## Technology Stack

Frontend:
- React
- Vite
- Tailwind CSS or equivalent

Backend:
- FastAPI
- Python
- SQLAlchemy or equivalent ORM
- Alembic or equivalent migration framework

Database:
- Self-hosted PostgreSQL on the OpenClaw computer

Local AI:
- Ollama
- qwen3:4b only

Paid AI:
- ChatGPT as primary development/reasoning provider
- Anthropic as fallback provider if ChatGPT token limits are reached

## GitHub Repository Requirements

Create a GitHub repository and store:

- Application source code
- Backend code
- Frontend code
- Worker code
- Database migrations
- Docker Compose files
- Documentation source files
- Generated PDFs
- OpenClaw reinstall prompts
- Backup and restore scripts
- ASVS audit files
- README
- CHANGELOG
- `.env.example`

Do not store:

- Real API keys
- Real `.env` files
- Wallet private keys
- Seed phrases
- Exchange withdrawal keys

## Repository Structure

```text
/crypto-wallet-intelligence
  /backend
  /frontend
  /workers
  /database
    /migrations
    /seed
  /docs
    /source
      First Installation.md
      Installation Guide.md
      User Guide.md
      ASVS Audit Template.md
    /pdf
      First Installation.pdf
      Installation Guide.pdf
      User Guide.pdf
      ASVS Audit (App version number).pdf
    /openclaw-prompts
      00_Initial_Kickoff_Prompt.md
      01_Project_Reinstall_Prompt.md
      02_Ollama_Setup_Prompt.md
      03_Anthropic_Fallback_Setup_Prompt.md
      04_PostgreSQL_Setup_Prompt.md
      05_Backup_Restore_Prompt.md
      06_ASVS_Audit_Update_Prompt.md
  /memory
  /agents
  /security
    /asvs
  /backup
  /docker
  /scripts
  README.md
  CHANGELOG.md
  .gitignore
  .env.example
  docker-compose.yml
```

## Documentation Requirements

The project must include:

- `First Installation.pdf`
- `Installation Guide.pdf`
- `User Guide.pdf`
- `ASVS Audit (App version number).pdf`

Rules:

- PDF documents must be generated from source files in `/docs/source`.
- Documentation must be updated after relevant development changes.
- The ASVS Audit PDF filename must include the application version being audited.
- The ASVS version used must be recorded inside the audit document.
- `Installation Guide.pdf` and `User Guide.pdf` must be kept current.
- `ASVS Audit (App version number).pdf` must be updated when requested or after security-relevant changes.

## Latest OWASP ASVS Requirement

The application must be developed against the latest stable release of the OWASP Application Security Verification Standard at the time of development or audit.

Security target:

- Minimum ASVS audit score: 90%

Score calculation:

```text
Passed applicable controls / Applicable controls x 100
```

Controls marked Not Applicable must include a reason.

The ASVS version used must be recorded in:

- ASVS Control Register
- ASVS Audit PDF
- README
- CHANGELOG when updated

## PostgreSQL Requirements

- PostgreSQL must run locally or in Docker on the OpenClaw computer.
- PostgreSQL must not be exposed directly to the internet.
- Credentials must be stored in environment variables.
- Database migrations must be enabled.
- UUID primary keys should be used where suitable.
- JSONB fields should be used for raw API payloads and decision snapshots.

Required extensions:

- pgcrypto
- uuid-ossp

Optional future extensions:

- pgvector
- TimescaleDB

## Ollama Requirements

Install Ollama early.

Only use:

```bash
ollama pull qwen3:4b
```

Use qwen3:4b for:

- Scraped text cleanup
- Webpage content extraction
- Token name extraction
- Wallet address extraction
- Transaction summary cleanup
- Headline classification
- News sentiment classification
- Event tagging
- Duplicate headline detection
- Simple alert wording
- First-pass research note drafts
- Formatting short reports
- Basic categorisation of wallet movement types

Do not use qwen3:4b alone for:

- Final financial recommendations
- Final copy-trade reasoning
- Risk-heavy judgement
- Complex multi-wallet strategy analysis
- Live trading decisions
- Anything involving real-money execution

## Paid Model Routing

Development routing:

1. Use qwen3:4b for safe, low-risk extraction and simple processing.
2. Use a cost-effective ChatGPT model for normal development and reasoning.
3. If ChatGPT token limits are reached, fall back to Anthropic.
4. Use higher-capability paid models only when the reasoning risk requires it.

Production/research-use routing:

1. qwen3:4b handles low-risk preprocessing.
2. Latest suitable paid models handle final risk scoring, high-confidence candidate reasoning and complex pattern analysis.

## Stage 0 Core Tables

- settings
- agent_logs
- model_task_logs
- tokens
- token_price_snapshots
- research_sources
- research_notes
- blocked_tokens

## Stage 0 Settings

Default settings:

- broad_market_search_enabled = false
- whale_wallet_monitoring_enabled = true
- pattern_intelligence_enabled = true
- paper_trading_enabled = true
- live_trading_enabled = false
- require_manual_approval_for_live_trades = true
- emergency_stop_enabled = false
- copy_trade_candidate_alerts_enabled = true
- ollama_enabled = true
- default_local_model = qwen3:4b
- paid_model_escalation_enabled = true

## Supported Chains for V1

Phase 1:

- Ethereum

Phase 1.1:

- Base
- Arbitrum

Optional later:

- Solana, only if the selected provider supports it cleanly

## Primary Data Providers

Initial provider targets:

- Wallet data: Moralis or Etherscan-compatible API
- Market data: CoinGecko or equivalent
- Research: RSS feeds, controlled web search and official sources
- Database: PostgreSQL
- Local model: Ollama qwen3:4b
- Paid reasoning: ChatGPT primary, Anthropic fallback

## Blocked Tokens Foundation

Create a blocked token list early.

Blocked token rules:

- Blocked tokens must not create copy-trade candidates.
- Blocked tokens may still appear in wallet movement history.
- Stablecoins should be tracked for flow analysis but should not become copy-trade candidates unless explicitly allowed.

## Duplicate Wallet Handling

Rules:

- Prevent duplicate wallet address + chain combinations.
- Normalise wallet addresses before saving.
- One wallet may have multiple tags but only one main wallet record per chain.

## Decision Snapshot Foundation

Add `decision_snapshot_json` to:

- agent_alerts
- copy_trade_candidates
- paper_trades
- wallet_pattern_matches

Decision snapshots must include:

- Wallets involved
- Token involved
- Pattern scores
- Data quality score
- Liquidity score
- Source reliability score
- Too-late score
- Risk score
- Confidence score
- Model used
- Research summary
- Rules that passed
- Rules that blocked the candidate
- Timestamp

## Backup and Restore Foundation

Add backup and restore scripts early.

Scripts:

- `/backup/backup_postgres.sh`
- `/backup/restore_postgres.sh`
- `/backup/backup_app_config.sh`
- `/backup/restore_app_config.sh`

Backup must include:

- Database schema
- Database data
- Settings
- Wallets
- Wallet movements
- Patterns
- Research notes
- Paper trades
- Logs
- ASVS records
- Documentation source files

Backup must not include unencrypted secrets.

## Stage 0 Success Criteria

Stage 0 is complete when:

- GitHub repository exists.
- React frontend skeleton runs.
- FastAPI backend skeleton runs.
- PostgreSQL is connected.
- Database migrations work.
- Ollama is installed and qwen3:4b responds.
- ChatGPT is configured as primary paid model.
- Anthropic is configured as fallback paid model.
- Settings page exists.
- ASVS register exists.
- Backup/restore scripts exist.
- First Installation.pdf exists.
- Installation Guide.pdf exists or has a current source draft.
- User Guide.pdf exists or has a current source draft.
- No secrets are exposed.

---

# Stage 1 - Whale Wallet Database and Movement Tracking

## Goal

Build the wallet database, wallet management UI and wallet movement polling.

## Core Tables

- whale_wallets
- wallet_movements
- watchlist

## Whale Wallets Page

Wallets must support:

- Add
- Edit
- Enable
- Disable
- Tag
- Classify
- Mark copy-trade enabled or disabled
- Mark Do Not Copy

Wallet fields:

- Wallet address
- Chain/network
- Label
- Wallet type
- Notes
- Enabled status
- Alert threshold in USD
- Watch priority
- Confidence weighting
- Copy-trade enabled status
- Last seen date/time
- Tags/sectors of interest
- Created date/time
- Updated date/time

Wallet types:

- Unknown
- Whale
- Smart Money
- VC/Fund
- Exchange
- Market Maker
- Influencer Wallet
- Developer Wallet
- Suspicious
- Do Not Copy

## Wallet Movement Tracking

Track:

- DEX buy
- DEX sell
- CEX deposit
- CEX withdrawal
- Wallet-to-wallet transfer
- Bridge movement
- Stablecoin accumulation
- Stablecoin deployment
- New token position
- Position increase
- Position reduction
- Full exit

Movement fields:

- Wallet ID
- Chain
- Transaction hash
- Movement type
- Token symbol
- Token contract
- Token amount
- Estimated USD value
- From address
- To address
- DEX/CEX/protocol involved
- Block number
- Transaction time
- Price at trade time
- Gas fee
- Alert threshold crossed
- Processed by agent
- Raw API payload JSONB
- Created date/time
- Updated date/time

## Data Quality Score

Add Data Quality Score from 0 to 100.

Store it on:

- wallet_movements
- wallet_signal_clusters
- wallet_pattern_matches
- copy_trade_candidates
- agent_alerts

Consider:

- Transaction verification
- Token contract match
- Price availability
- Liquidity availability
- Movement classification confidence
- Real trade vs transfer
- Estimated vs confirmed token value
- Agreement across sources
- Chain identification
- Protocol identification

Low data quality should trigger manual review and prevent automatic candidate creation.

## Manual Review Required Flag

Add `manual_review_required` to:

- wallet_movements
- wallet_signal_clusters
- wallet_pattern_matches
- agent_alerts
- copy_trade_candidates

Manual review is required when:

- Data quality is low
- Liquidity is low
- Token is new or unknown
- Token contract is unverified
- Research sources conflict
- Wallet type is Unknown, Suspicious, Developer Wallet or Influencer Wallet
- Too-late score is high
- Price data is missing
- Token appears on Blocked Tokens list

## Stage 1 Success Criteria

- Wallets can be managed.
- Enabled wallets are checked.
- Wallet movements are stored.
- Data quality is scored.
- Large movements generate alerts.
- Manual review flags work.
- Raw API payloads are stored.

---

# Stage 2 - Price Outcomes and Signal Validation Loop

## Goal

Measure whether wallet signals actually work.

## Core Table

- wallet_trade_outcomes

## Price Outcome Tracking

For every wallet movement, track:

- Price at trade time
- Price after 15 minutes
- Price after 1 hour
- Price after 4 hours
- Price after 24 hours
- Price after 7 days
- Max gain within 24 hours
- Max drawdown within 24 hours
- Max gain within 7 days
- Max drawdown within 7 days
- Outcome score

## Signal Expiry and Confidence Decay

Add:

- expires_at
- confidence_decay_started_at
- original_confidence_score
- current_confidence_score
- expired_reason

Default examples:

- Large wallet movement alert: 4 hours
- Copy-trade candidate: 30 minutes
- CEX deposit risk alert: 24 hours
- Whale trend cluster: 4 hours

Expired candidates must not create paper trades.

## Stage 2 Success Criteria

- Outcomes are recorded.
- Wallet performance can be measured.
- Signal expiry works.
- The system can show whether a wallet signal was useful.

---

# Stage 3 - Core Pattern Intelligence

## Goal

Detect the highest-value wallet patterns first.

## Core Tables

- wallet_pattern_rules
- wallet_pattern_matches
- wallet_signal_clusters
- wallet_signal_cluster_members
- wallet_relationships
- wallet_influence_scores

## V1 Pattern Types

Build these first:

1. Price rise after wallet buy
2. Price drop after wallet sell
3. Leader/follower wallet pattern
4. Coordinated accumulation
5. Coordinated exit
6. CEX deposit before drop
7. CEX withdrawal before rise
8. Stablecoin deployment
9. Stablecoin accumulation
10. Sudden behaviour change
11. Probe-then-commit
12. Too-late score

## Too-Late Score

Create a Too-Late Score from 0 to 100 using:

- Price when first wallet entered
- Current price
- Percentage move since first wallet entry
- Spread
- Liquidity
- Estimated slippage
- Volume spike
- Time elapsed
- Whether the move has already played out

High too-late score should block copy-trade candidates.

## Minimum Liquidity Rule

Configurable settings:

- minimum_liquidity_usd_for_candidate
- minimum_24h_volume_usd_for_candidate
- maximum_estimated_slippage_percent
- allow_low_liquidity_watch_alerts = true
- allow_low_liquidity_copy_trade_candidates = false

Low liquidity can create watch alerts but not copy-trade candidates.

## Wallet Influence Score

Score 0 to 100 based on:

- Price movement after trades
- Average gain after buys
- Average drop after sells
- Buy hit rate
- Sell hit rate
- Follower relationships
- Trade size
- Liquidity
- Signal consistency
- False signal rate

## Stage 3 UI Pages

- Whale Trend Clusters
- Wallet Relationships
- Pattern Alerts
- Wallet Influence Report

## Stage 3 Success Criteria

- Core patterns are detected.
- Too-late scoring works.
- Liquidity gating works.
- Influence scores are calculated.
- Pattern alerts are visible.

---

# Stage 4 - Research Agent and Controlled Web Research

## Goal

Research coins only when wallet activity creates a reason to research.

## Research Triggers

Trigger research only when:

- A large wallet movement is detected
- A whale trend cluster is detected
- A core pattern is detected
- A copy-trade candidate is being assessed
- A token is manually added to watchlist
- The user manually requests research

## Source Reliability Score

Score sources from 0 to 100.

Examples:

- Official project announcement: high
- Exchange announcement: high
- Official governance/GitHub: high
- Major crypto news site: medium
- Random blog/social post: low
- Unverified rumour: very low

Low-reliability sources must not create high-confidence recommendations.

## Secure Web Research Controls

- Treat scraped content as untrusted.
- Limit page size.
- Limit pages per research task.
- Set timeouts.
- Block internal IP ranges to reduce SSRF risk.
- Do not execute code from scraped content.
- Do not follow unlimited redirects.
- Escape/sanitise displayed scraped content.

## Prompt Injection Protection

Scraped content must never:

- Override system instructions
- Request secrets
- Control tools
- Trigger trading actions
- Disable security

The model must summarise content, not obey it.

## Stage 4 Success Criteria

- Wallet-triggered research works.
- qwen3:4b handles low-risk cleanup and extraction.
- Paid model escalation works.
- Source reliability is scored.
- Research notes link back to triggering movements or patterns.

---

# Stage 5 - Copy-Trade Candidates and Paper Trading

## Goal

Create scored copy-trade candidates and test them with paper trading only.

## Core Tables

- copy_trade_candidates
- paper_portfolios
- paper_positions
- paper_trades

## Candidate Creation Rules

Candidates can only be created when:

- Pattern confidence is above threshold
- Too-late score is acceptable
- Liquidity is acceptable
- Risk score is acceptable
- Data quality is acceptable
- Source reliability is acceptable
- Wallet is not Do Not Copy
- Token is not blocked
- Emergency stop is off
- Paper trading is enabled
- Supporting evidence exists

## Candidate Fields

- Token
- Chain
- Suggested action
- Suggested entry
- Stop loss
- Take profit
- Max paper position size
- Copy-trade suitability score
- Too-late score
- Risk score
- Signal confidence score
- Reasoning
- Supporting wallet movements
- Supporting pattern matches
- Research summary
- Status
- Decision snapshot JSONB

## No-Live-Trading Enforcement

Add validation proving:

- No live exchange execution endpoint is active.
- `live_trading_enabled` defaults to false.
- Emergency stop blocks trading workflows.
- Paper trading is clearly separated from live trading.
- No withdrawal key fields exist.
- Candidate creation does not equal execution.
- Local model output cannot execute trades.

## Stage 5 Success Criteria

- Candidates are generated from strong wallet patterns.
- Bad candidates are blocked.
- Paper trades can be created.
- Paper P&L is tracked.
- Decision snapshots are stored.
- No live trading is possible.

---

# Stage 6 - Reporting and Feedback Optimisation

## Goal

Make the system learn which wallets, patterns and signals are useful.

## Reports

Add reports for:

1. Most accumulated coins by watched wallets
2. Most sold coins by watched wallets
3. Wallet performance by 15m, 1h, 4h, 24h and 7d outcomes
4. Best first-mover wallets
5. Best confirmation wallets
6. Worst false-signal wallets
7. Wallets that frequently follow others
8. Possible coordinated wallet groups
9. Missed opportunities
10. Bad signals
11. CEX deposit risk report
12. CEX withdrawal accumulation report
13. Stablecoin deployment/risk-on report
14. Stablecoin accumulation/risk-off report
15. Copy-trade candidate performance
16. Paper trading performance
17. Pattern performance by type
18. Data quality report
19. Liquidity/slippage report
20. Source reliability report
21. Decision audit report
22. ASVS score report
23. Backup and restore report
24. Documentation freshness report
25. Model usage and cost-reduction report

## Stage 6 Success Criteria

- Reports show which wallets work.
- Reports show which patterns work.
- Reports show why candidates were created or blocked.
- Reports show model usage.
- Reports show backup and documentation status.

---

# Stage 7 - V1.1 Enhancements

## Goal

Add useful features after V1 works.

## Features

- External notifications: email, webhook, Telegram/Signal if practical
- Manual Review Queue page
- Relationship graph
- Additional pattern types
- Documentation generation automation
- Migration assistant
- Restore test mode

## Additional Pattern Types

- Sell/buy divergence
- Bridge movement
- Chain rotation
- New wallet funded by known wallet
- Same funding source
- Split-buy accumulation
- DCA/routine accumulation
- Dormant wallet wakes up
- Pre-listing accumulation
- Unlock-risk pattern
- Liquidity add pattern
- Liquidity removal pattern
- Pump-and-distribute pattern
- Whale buys after negative news
- Whale sells after positive news
- Repeated time-of-day pattern
- Gas-fee urgency pattern
- Position sizing change
- Failed breakout wallet exit
- Holding-period pattern
- Related-wallet exit before main wallet

---

# Stage 8 - V2 Advanced Intelligence

## Goal

Add advanced analysis once the core system proves useful.

## Features

- Backtesting engine
- Advanced provider comparison
- Cross-chain same-token pattern
- Top-holder concentration change
- Liquidity-following wallet
- Wallet exits while public hype increases
- Wash-trading/self-transfer pattern
- Smart-wallet sector overlap
- Public hype comparison
- Social sentiment comparison
- Multi-chain wallet identity inference
- Optional pgvector
- Optional TimescaleDB
- ASVS improvement sprint
- Encrypted backups
- Disaster recovery drill

---

# Stage 9 - V3 Controlled Live Trading

## Goal

Only consider live trading after paper trading and backtesting prove the system.

## Preconditions

Do not consider live trading until:

- At least 30 days of paper trading exists.
- Backtesting supports the rules.
- Data quality scoring has been active for at least 30 days.
- Liquidity rules have been active for at least 30 days.
- Decision snapshots exist for all candidates.
- Manual review queue has been tested.
- Too-late scoring has been validated.
- Paper-trade performance is profitable after fees and slippage.
- Emergency stop works.
- All live trades require manual approval.
- No withdrawal permissions exist.

## Live Trading Rules, If Ever Added

- Manual approval required for every trade.
- No withdrawals.
- No margin.
- No leverage.
- No futures.
- Max position size enforced.
- Max daily loss enforced.
- Max open exposure enforced.
- Emergency stop enforced.
- Every trade logged.

---

# Security Rules for All Stages

1. Do not store API keys in frontend code.
2. Store credentials in environment variables.
3. Do not expose Ollama directly to the internet.
4. Do not expose PostgreSQL directly to the internet.
5. Log which model handled each agent task.
6. Log paid model escalation.
7. Never allow a local model to execute real trades.
8. Never allow a model to access withdrawal permissions.
9. Emergency stop overrides trading workflows.
10. Do not install untrusted crypto plugins or OpenClaw skills.
11. Do not expose admin pages publicly.
12. Fail safely if API keys or market data are missing.
13. Keep all V1 trade execution disabled.

# V1 Success Criteria

V1 is successful when:

1. The app runs locally on the OpenClaw computer.
2. The project is saved in GitHub.
3. PostgreSQL is the main database.
4. Ollama works with qwen3:4b only.
5. ChatGPT is primary and Anthropic fallback is configured.
6. Wallets can be added, edited, enabled and disabled.
7. Wallet movements are detected and stored.
8. Data Quality Score is calculated.
9. Large wallet movements create alerts.
10. Price outcomes are tracked.
11. Core wallet patterns are detected.
12. Too-late scoring works.
13. Minimum liquidity rules are enforced.
14. Source reliability scoring works.
15. Decision snapshots are stored.
16. Wallet influence scores are calculated.
17. Research notes are generated from wallet-triggered events.
18. Copy-trade candidates are scored.
19. Paper trades can be created and tracked.
20. Reports show wallet and pattern performance.
21. Emergency stop works.
22. No live trading is possible.
23. No secrets are exposed.
24. Backup and restore scripts exist.
25. Restore process has been tested at least once.
26. First Installation.pdf exists.
27. Installation Guide.pdf exists and is current.
28. User Guide.pdf exists and is current.
29. ASVS Audit (App version number).pdf exists and is current.
30. Latest stable OWASP ASVS version has been checked and recorded inside the audit.
31. ASVS audit score is at least 90% across applicable controls.
32. OpenClaw reinstall prompt documentation exists.
33. README explains setup, environment variables and how to run locally.
