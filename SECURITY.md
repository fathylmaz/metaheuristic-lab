# Security — local-only scope

Metaheuristic Lab is a single-user educational/research application designed for local execution.

- Docker publishes the web port on **127.0.0.1:5173** only; the API has no public host port in Compose.
- There is **no login, authorization, tenant isolation, TLS termination, audit of user identity, distributed rate limiting or remote secret management**. Do not expose the service to untrusted networks or host it publicly in its current form.
- `.env*`, `backend/data/`, `backups/`, `outputs/`, browser test artifacts, and local profiles must not be committed.
- Local experiment data may contain sensitive names or proprietary problem inputs. Inspect every exported report and screenshot before sharing.
- API input limits and safety middleware provide bounded local use, **not a security certification**.
- Backup before upgrades using `py -3.13 .\\scripts\\backup_experiments.py` and verify the generated archive.
- If a security issue is discovered, coordinate privately with the repository owner; do not post private database contents in public issues.

See [docs/DEPLOY_LOCAL.md](docs/DEPLOY_LOCAL.md) for deployment and backups.
