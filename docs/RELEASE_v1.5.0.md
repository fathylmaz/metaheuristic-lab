# Metaheuristic Lab v1.5.0 — Simulated Annealing

- **13 of 15 algorithms ready.** Added SA as a **single-solution** optimizer, not a fictitious group of agents.
- Python simulation: geometric temperature schedule, Gaussian neighbor candidate, Metropolis acceptance of worse candidates, bounded coordinates, independent best-ever archive, one real function evaluation for every candidate including rejected proposals.
- Interactive canvas: evaluated accepted/rejected candidate, current position and archived best. Selected current point exposes candidate coordinates, delta, probability, uniform draw, step, acceptance decision and temperature.
- SA statistics: current temperature, cumulative acceptances, uphill acceptances and rejected proposals; separate logarithmic temperature curve with decision markers.
- Config: `sa_initial_temperature`, `sa_cooling_rate`, `sa_step_scale`.
- `backend/tests/test_annealing.py` adds **11 unit/API tests**. Full Python suite: **141 passed**.
- TypeScript/TSX syntax validated using the TypeScript compiler API. Full frontend production build remains to be checked on Windows with `npm.cmd run build`.
- All previous 12 algorithms, ACO graph lab, three-way comparison, and SQLite history are kept unchanged; SA is **not yet** integrated into equal-NFE benchmark comparisons.
- Archive contains the top-level `metaheuristic-lab/` directory and no `.git`, `.venv`, `node_modules`, databases or user results. Update existing project by extracting to its parent `C:\VS CODE PROJE` with overwrite (`-Force`).

Background: Kirkpatrick, Gelatt & Vecchi (1983), *Optimization by Simulated Annealing*, Science, DOI 10.1126/science.220.4598.671. Mathematical conventions: `docs/SA_METHODOLOGY.md`.
