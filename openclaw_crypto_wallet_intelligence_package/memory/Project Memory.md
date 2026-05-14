# Project Memory

The project is a self-hosted crypto wallet intelligence and paper-trading app running on the same Ubuntu 24.04 computer as OpenClaw.

The app monitors whale wallets, records movements, detects wallet behaviour patterns, researches wallet-triggered token activity, creates copy-trade candidates for paper trading only, and reports which wallets and patterns actually work.

The system must be wallet-led by default. Broad market search is disabled by default.

V1 is research and paper-trading only. No live trading.

Core technologies:
- OpenClaw
- PostgreSQL
- Ollama qwen3:4b only
- FastAPI
- React + Vite
- ChatGPT primary paid model
- Anthropic fallback paid model

Security requirements:
- Develop against the latest stable OWASP ASVS at time of development or audit.
- Target ASVS score is 90% or higher.
- No secrets in GitHub.
- No wallet private keys.
- No seed phrases.
- No withdrawal keys.
- No live trading in V1.
