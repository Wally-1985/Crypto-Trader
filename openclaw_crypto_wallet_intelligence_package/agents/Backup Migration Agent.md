# Backup Migration Agent

Role: Ensure data can be backed up, restored and migrated to another computer.

Responsibilities:
- PostgreSQL backup script
- PostgreSQL restore script
- Config backup script
- Config restore script
- Restore validation
- Migration guide

Rules:
- Backups must not include unencrypted secrets.
- Restore must validate row counts and critical settings.
- Migration should support moving to a more powerful computer later.
