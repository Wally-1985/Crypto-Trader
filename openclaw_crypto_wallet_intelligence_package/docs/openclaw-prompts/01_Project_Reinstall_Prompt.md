# 01 - Project Reinstall Prompt

Use this prompt when reinstalling or migrating the system to another computer.

You are rebuilding the Crypto Wallet Intelligence and Paper Trading App from GitHub.

Inputs to confirm before starting:
- Repository URL: {{PROJECT_REPOSITORY_URL}}
- Target Ubuntu version: {{UBUNTU_VERSION}}
- PostgreSQL restore file: {{POSTGRES_BACKUP_FILE}}
- App version: {{APP_VERSION}}
- Ollama model: qwen3:4b

Tasks:
1. Clone the GitHub repository.
2. Review README and First Installation guide.
3. Install required system packages.
4. Install PostgreSQL or start PostgreSQL through Docker Compose.
5. Restore PostgreSQL backup if provided.
6. Install Ollama if not installed.
7. Pull `qwen3:4b` only.
8. Configure `.env` from `.env.example`.
9. Confirm ChatGPT primary model access.
10. Configure Anthropic fallback access.
11. Run database migrations.
12. Start backend.
13. Start frontend.
14. Start background workers.
15. Run restore validation.
16. Run security checks for exposed services.
17. Confirm documentation PDFs exist.
18. Summarise the reinstall result.

Do not expose PostgreSQL or Ollama to the internet.
Do not commit real secrets.
Do not enable live trading.
