# Database Migrations

Stage 0 migration foundations live here.

Included foundation SQL:

- `0001_stage0_model_task_logs.sql` — enables `pgcrypto` and `uuid-ossp`, then creates `model_task_logs` for safe provider/fallback event logging.

Migration runner:

```bash
./scripts/db_migrate.sh
```

The runner creates a `schema_migrations` table before applying SQL files in filename order. It requires `psql` and uses these environment variables when set:

- `POSTGRES_HOST` default `127.0.0.1`
- `POSTGRES_PORT` default `5432`
- `POSTGRES_DB` default `crypto_wallet_intelligence`
- `POSTGRES_USER` default `cwi_app`

Initial migration work must enable PostgreSQL extensions:

- `pgcrypto`
- `uuid-ossp`

Future schema work should use UUID primary keys where suitable and JSONB for raw API payloads and decision snapshots.
