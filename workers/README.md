# Workers

Stage 0 placeholder for background workers.

Workers must respect:

- V1 paper-trading only.
- Broad market search disabled by default.
- Emergency stop overrides candidate workflows.
- Model output must never directly execute shell commands, trades, or security changes.
