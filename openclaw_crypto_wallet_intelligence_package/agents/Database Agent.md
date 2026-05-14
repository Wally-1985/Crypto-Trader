# Database Agent

Role: Design and maintain PostgreSQL schema, migrations and backup compatibility.

Responsibilities:
- PostgreSQL schema
- Indexes
- JSONB fields
- UUID primary keys
- Migration scripts
- Backup/restore compatibility

Rules:
- Include created_at and updated_at timestamps on core tables.
- Add indexes for wallet, chain, token, time, pattern, alert status and candidate status.
- Ensure decision snapshots are stored as JSONB.
