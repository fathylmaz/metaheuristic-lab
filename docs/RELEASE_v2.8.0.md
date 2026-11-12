# Metaheuristic Lab v2.8.0 - Release quality and verification

This release does **not** claim to make the project production-safe for untrusted public traffic. It adds reproducible release checks while preserving the mathematical core and experiment data.

## Changes
- A 1 MiB request-body cap on POST `/api/*` endpoints (both Content-Length and streamed bodies).
- Defensive HTTP headers: `X-Content-Type-Options`, `Referrer-Policy`, `X-Frame-Options` and `Cache-Control` on API responses. Existing HTML report CSP remains unchanged.
- New backend API safety and archive/report integration checks.
- Playwright browser smoke tests for the app, navigation, algorithm selection and invalid API requests.
- CI now runs the browser tests with a clean Python backend and Vite frontend on a fresh Linux worker.
- `scripts/verify_windows.ps1` runs backend tests, API checks, frontend build, and browser smoke tests when available.
- All UI and API version indicators updated to v2.8.0.

## Run on Windows

```powershell
cd 'C:\VS CODE PROJE\metaheuristic-lab'
powershell -ExecutionPolicy Bypass -File .\scripts\verify_windows.ps1
```

To enable browser tests, once in `frontend`:

```powershell
npm.cmd install
npx.cmd playwright install chromium
npm.cmd run test:e2e
```

Both API and frontend servers are started by Playwright automatically if ports 8000/5173 are free. The tests work with existing local servers in developer mode.

## Scope and limitations
- Playwright tests are smoke tests, not full visual regression or comprehensive user journeys.
- No accounts, role-based permissions, login, rate limiting or remote multi-user isolation are provided. Keep the web service bound to localhost in development.
- For internet deployment add an authenticated reverse proxy, HTTPS, rate limiting, persistent volumes and operational monitoring.
- API request limits guard against accidental large JSON uploads but do not bound the CPU time of every supported benchmark; larger experiments need a job queue before a public deployment.
- Experiment records in `backend/data` are **never** included in the ZIP.

## Descriptive performance profile

From `backend`, run `python ../scripts/profile_api.py --repeats 5 --iterations 20`.
This prints measured response times and real NFE values. No machine-specific
performance threshold is used as a gate; for comparative performance runs,
keep the hardware, process state and workload fixed.
