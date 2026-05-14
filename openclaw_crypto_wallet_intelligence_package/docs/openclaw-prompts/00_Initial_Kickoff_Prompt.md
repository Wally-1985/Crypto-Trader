# 00 - Initial OpenClaw Kickoff Prompt

Use the repository files and project memory provided.

Begin Stage 0 only. Do not build application features yet.

Your goals are:

1. Review `DEVELOPMENT_PLAN.md`.
2. Review all files in `/memory` and `/agents`.
3. Confirm the repository structure.
4. Create or validate the FastAPI backend skeleton.
5. Create or validate the React + Vite frontend skeleton.
6. Configure PostgreSQL using the provided `docker-compose.yml` or a native local PostgreSQL install.
7. Install and test Ollama using only `qwen3:4b`.
8. Configure model routing so qwen3:4b handles low-risk local tasks.
9. Configure ChatGPT as the primary paid development model.
10. Add Anthropic fallback routing quickly, so development can continue if ChatGPT token limits are reached.
11. Use cost-effective paid models during development where suitable.
12. Create the ASVS audit/register foundation and record that the latest stable OWASP ASVS version must be checked at audit time.
13. Create or validate the backup and restore script foundations.
14. Create or validate documentation source files.
15. Update README and CHANGELOG if anything changes.

Stop after Stage 0 validation.

Do not create live trading features.
Do not request or store wallet private keys.
Do not commit secrets.
