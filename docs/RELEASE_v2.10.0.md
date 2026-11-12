# Metaheuristic Lab v2.10.0 — Persistent Dimensional Job Queue

## New

- SQLite-backed local job queue with 202 accepted response and status polling.
- Progress by independent algorithm/seed trial, visible in the new **Deney Kuyruğu** navigation tab.
- Cooperative cancellation between trials; pending jobs are cancelled without execution.
- Jobs persist across application restarts. In-progress jobs replay from the beginning, **not** from a partial numerical checkpoint.
- Successful jobs are atomically archived alongside status updates and become available in High-Dimensional and Academic Reports archives.
- At most one running job and eight active tasks; failures are isolated and do not block the next task.
- Extended backend regression and browser-level end-to-end coverage.

## Intentionally not included

- No cloud worker, multi-process scheduler, or authentication; keep local-only.
- No partial-trial interruption or exact CPU progress percentage.
- No background processing for other experiment types in this version.

## Migration

Extract this ZIP into `C:\VS CODE PROJE` so it overlays the existing `metaheuristic-lab` folder. Stop prior servers before updating. It has **no** `.venv`, `node_modules`, `.git` or SQLite database files. Existing experiment archives stay intact.

## Verify

```powershell
cd "C:\VS CODE PROJE\metaheuristic-lab\backend"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

In a separate terminal:

```powershell
cd "C:\VS CODE PROJE\metaheuristic-lab\frontend"
npm.cmd run build
npm.cmd run dev
npm.cmd run test:e2e
```

Open `http://127.0.0.1:5173` -> `Deney Kuyruğu`, select 2–4 algorithms, enqueue, and inspect the recorded result.
