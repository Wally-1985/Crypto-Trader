# Database Migrations

Stage 0 placeholder for Alembic migrations.

Initial migration work must enable PostgreSQL extensions:

- `pgcrypto`
- `uuid-ossp`

Future schema work should use UUID primary keys where suitable and JSONB for raw API payloads and decision snapshots.
