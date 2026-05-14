# 05 - Backup and Restore Prompt

Implement and test backup and restore capability.

Tasks:
1. Review `/backup` scripts.
2. Implement PostgreSQL backup using `pg_dump` custom format.
3. Implement PostgreSQL restore using `pg_restore`.
4. Implement app config backup without secrets.
5. Implement app config restore.
6. Add restore validation checks.
7. Confirm important tables are included.
8. Confirm ASVS and documentation records are included where stored in the database.
9. Update Installation Guide.
10. Add a backup and restore report to Stage 6 when reporting exists.

Rules:
- Do not include unencrypted secrets in backups.
- Do not commit backup files to GitHub.
- Backups should support migration to a more powerful computer later.
