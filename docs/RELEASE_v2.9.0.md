# Metaheuristic Lab v2.9.0 — Local release readiness

## Scope

This release does **not** change any optimization algorithm equations or experiment results. It focuses on dependable local Docker packaging, persistent archive backups, operational checks and documentation.

### Added
- Multi-stage Node build -> static Nginx web server (`frontend/Dockerfile`, `frontend/nginx.conf`); no Vite dev server in Docker.
- Same-origin `/api/` reverse proxy; only `127.0.0.1:5173` is exposed to the host. Backend remains internal to Compose.
- Docker health checks and start-after-healthy dependency.
- SQLite online backup + SHA-256 manifest and validation (`scripts/backup_experiments.py`), including tests for corruption and non-overwrite behavior.
- Windows Docker smoke command (`scripts/verify_docker_windows.ps1`).
- GitHub Actions Docker smoke job (requires Docker runner).
- v2.9.0 version labels and refreshed instructions; local backup ZIPs ignored by Git.

### Intentional limitations
- Synchronous experiment execution and no durable job queue, cancellation or live progress. Reverse proxy timeout may be reached on very long experiments.
- Only local-machine deploy is supported; no login/auth, TLS or rate limiting. Do not expose the container port to the public Internet.
- Lockfiles for frontend and fully pinned Python dependencies are not part of this release. Runtime versions should be locked before reproducible institutional deployments.
- This environment can run backend pytest but cannot run Docker or npm production build; Windows and GitHub CI checks are separate validation gates.

### Validation
- All backend pytest tests including five new SQLite backup tests must pass.
- `npm.cmd run build`, `npm.cmd run test:e2e` and Docker smoke must be verified on Windows/CI.
- SQLite backups can be verified independently with `--verify`; backing up while a transaction is open is safe thanks to SQLite's online backup API.
