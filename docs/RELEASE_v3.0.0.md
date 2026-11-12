# Metaheuristic Lab v3.0.0 — Final research/portfolio release

**2026-11-12.** Final local-first research release, **not** a public hosted production service.

## What is complete

- The planned 15 algorithm simulation engines and ACO's separate TSP laboratory.
- D-dimensional benchmark of 14 continuous optimizers (2/5/10/30D) with 5 objective families, seeded repeats and explicit NFE.
- Comparison, benchmark matrix, OFAT, dimensional, archived scientific reporting, science audit, local persistent jobs/checkpoints.
- Desktop and mobile-oriented React UI, lazy-loaded labs, accessible navigation, local Docker/Nginx distribution.
- Test coverage in Pytest and Playwright and container check scripts.

## v3 changes from v2.15

- `3.0.0` version in FastAPI, health response and frontend package.
- GitHub Actions Docker health check now reads its expected version from `frontend/package.json` instead of using obsolete `2.9.0`.
- Bilingual concise README entry points, architecture/reproducibility/limitations documentation.
- Screenshot capture command, release audit and prepublication checklist.
- Academic presentation and publication kit distributed separately, without inventing unverified screenshots or a GitHub URL.
- Docker deployment guide revised to reflect the already implemented persistent job queue.

## Verified on Windows — 12 November 2026

The user executed the v3.0.0 Windows release checks: **547/547 Pytest backend tests, 30/30 API contract checks (a subset of the backend suite), 12/12 Playwright E2E tests, and a successful TypeScript/Vite build.** The Docker verification reported **API 3.0.0** and **healthy** API/web containers with local Nginx proxy checks. A `StarletteDeprecationWarning` appeared but did not fail the suite. Public GitHub Actions execution remains **unverified** until the repository is published.

A curated gallery of **23 real application captures** has been supplied and linked from both READMEs: [`docs/SCREENSHOT_GALLERY.md`](SCREENSHOT_GALLERY.md). The visible screenshots are provided for owner review; no public publishing action has occurred.

## Evidence and remaining actions

Windows release test outputs have been provided and reviewed as described above. CI jobs can only be claimed successful after execution on the actual GitHub repository.

Not done automatically: repository creation/push, public release, license selection, uploading local experimental records, publishing a LinkedIn post, or making screenshots of a non-running version.

See `docs/RELEASE_CHECKLIST.md` for the exact closing procedure.
