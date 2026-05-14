# 04 - PostgreSQL Setup Prompt

Set up PostgreSQL on the local Ubuntu 24.04 OpenClaw computer.

Tasks:
1. Decide whether to use Docker Compose or native PostgreSQL.
2. If using Docker Compose, use the included `docker-compose.yml` and keep PostgreSQL bound to `127.0.0.1`.
3. Create database and application user.
4. Enable required extensions: pgcrypto and uuid-ossp.
5. Configure `.env` from `.env.example`.
6. Create migration framework.
7. Create Stage 0 tables.
8. Add backup and restore scripts.
9. Confirm no secrets are committed.
10. Update Installation Guide.

Rules:
- Do not expose PostgreSQL to the internet.
- Use environment variables for credentials.
- Keep backup compatibility in mind from the beginning.
