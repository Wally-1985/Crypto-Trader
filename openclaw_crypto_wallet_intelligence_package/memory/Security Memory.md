# Security Memory

The project must be developed against the latest stable OWASP ASVS version at the time of development or audit.

Target score: at least 90% across applicable controls.

Core security rules:
- Do not commit secrets.
- Do not expose PostgreSQL to the internet.
- Do not expose Ollama to the internet.
- Use environment variables for credentials.
- Treat scraped content as untrusted.
- Protect against prompt injection in research content.
- Do not store wallet private keys or seed phrases.
- Do not store exchange withdrawal keys.
- V1 must not have live trade execution.
- Emergency stop must override trading workflows.
- Every important alert/candidate must have a decision snapshot.
