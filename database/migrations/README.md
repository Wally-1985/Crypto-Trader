# Database Migrations

Stage 0 migration foundations live here.

Included foundation SQL:

- `0001_stage0_model_task_logs.sql` — enables `pgcrypto` and `uuid-ossp`, then creates `model_task_logs` for safe provider/fallback event logging.

Initial migration work must enable PostgreSQL extensions:

- `pgcrypto`
- `uuid-ossp`

Future schema work should use UUID primary keys where suitable and JSONB for raw API payloads and decision snapshots.
