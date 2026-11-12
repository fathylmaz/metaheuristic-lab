# Metaheuristic Lab v0.3.0 — Comparison Laboratory

Date: 2026-11-11

## What's new
- `POST /api/comparisons` runs FA and PSO across identical 2D benchmark objective, population, iterations and seed list; the objective evaluation budget is equal for both methods.
- Reports mean, median, sample standard deviation, min/max, success rate, per-run results and mean convergence by function evaluations.
- Two replayable Canvas trajectories from **median-performing individual runs**, sharing an iteration timeline. These are NOT animations of the *mean* population.
- SQLite storage for **comparison experiments** with compressed full payload; list and reopen from the app, JSON/CSV export.
- New navigation section and algorithm-specific benchmark parameters.
- Docker Compose bind mount preserves SQLite records across container restarts.

## Status and limitations
- **FA and PSO are the only implemented algorithms**; other 13 catalog entries are placeholders.
- 36 Python tests passed in artifact environment; HTTP persistence smoke tests covered in Pytest.
- TypeScript/TSX syntax parser found zero parse errors; full Vite production build and browser UI NOT verified in artifact environment because npm registry access failed. Run `npm.cmd install` and `npm.cmd run build` locally.
- Benchmarks are synchronous and fully computed prior to displaying animation (not WebSocket streaming).
- Main single-simulation history remains in-memory; only comparisons are persisted to SQLite.
- Performance is empirical for the selected finite seed sample only and does not establish algorithm superiority on other tasks. Wall-clock duration is displayed but not normalized by CPU or background workload.
- `backend/data` is not part of update ZIPs; backup source edits before overlay, and backup SQLite before moving machines.

## Scientific definitions
- NFE budget = `population_size * (iterations + 1)` for each seed and algorithm.
- Curves show mean best-*so-far* value, aligned by objective function evaluation count.
- `std_best` is sample standard deviation (n - 1).
- Success if best-*so-far* objective value <= configurable positive success tolerance; currently known global optimum value is zero on the four provided benchmark functions.
- Both algorithms start from the same initial population for each seed because they share NumPy seeded uniform initialization; their subsequent algorithm-specific random draws differ.
- Median-performing representative run is for *visual inspection*, and does not claim to represent the average trajectory.
